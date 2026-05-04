import os
import glob
import logging
from pathlib import Path
import pyarrow as pa
import lancedb
from llama_cpp import Llama
from app import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

embedding_model = None
db = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        logger.info(f"Loading embedding model from {config.EMBEDDING_MODEL_PATH}")
        embedding_model = Llama(
            model_path=config.EMBEDDING_MODEL_PATH,
            n_ctx=config.EMBEDDING_N_CTX,
            n_threads=config.LLM_N_THREADS,
            embedding=True
        )
        logger.info("Embedding model loaded")
    return embedding_model

def get_db():
    global db
    if db is None:
        os.makedirs(config.INDEX_PATH, exist_ok=True)
        db = lancedb.connect(config.INDEX_PATH)
    return db

import re
from pypdf import PdfReader

def load_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        return ""

def semantic_chunk_text(text: str, max_chunk_size: int = 512, min_chunk_size: int = 100):
    """
    Split text by semantic boundaries (headings, paragraphs).
    Respects markdown headers (#, ##, ###) and paragraph breaks.
    """
    # Find all headers with their positions
    header_pattern = r'^(#{1,6})\s+(.+)$'
    header_matches = list(re.finditer(header_pattern, text, re.MULTILINE))
    
    if not header_matches:
        # No headers - use simple chunking
        return simple_chunk(text, max_chunk_size, min_chunk_size)
    
    chunks = []
    for i, match in enumerate(header_matches):
        start = match.start()
        end = match.end() if i + 1 < len(header_matches) else len(text)
        section = text[start:end].strip()
        
        if len(section) >= min_chunk_size:
            chunks.append(section)
        elif len(section) > 0:
            # Too small - add to previous or keep
            if chunks and len(chunks[-1]) + len(section) < max_chunk_size:
                chunks[-1] += "\n\n" + section
            else:
                chunks.append(section)
    
    # Handle any remaining text after last header
    last_header_end = header_matches[-1].end() if header_matches else 0
    remaining = text[last_header_end:].strip()
    if remaining and len(remaining) >= min_chunk_size:
        chunks.append(remaining)
    elif remaining and chunks and len(chunks[-1]) + len(remaining) < max_chunk_size:
        chunks[-1] += "\n\n" + remaining
    
    return [c for c in chunks if len(c) >= min_chunk_size]

def simple_chunk(text: str, chunk_size: int, overlap: int):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks
    
    chunks = []
    current_chunk = ""
    
    for section in sections:
        if not section.strip():
            continue
            
        # If section itself is a header
        if section.startswith('#'):
            # Save previous chunk if exists
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = section
        else:
            # Add content, split if too large
            if len(current_chunk) + len(section) < max_chunk_size:
                current_chunk += "\n" + section
            else:
                # Save current
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                # Split large sections
                current_chunk = section
    
    # Add remaining
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # If chunks are still too large, split them further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            # Split by sentences or lines
            sub_chunks = []
            lines = chunk.split('\n')
            temp = ""
            for line in lines:
                if len(temp) + len(line) < max_chunk_size:
                    temp += "\n" + line
                else:
                    if temp.strip():
                        sub_chunks.append(temp.strip())
                    temp = line
            if temp.strip():
                sub_chunks.append(temp.strip())
            final_chunks.extend(sub_chunks)
    
    # Filter out small chunks
    return [c for c in final_chunks if len(c) >= min_chunk_size]

# Alias for compatibility
chunk_text = semantic_chunk_text

def get_embedding(text: str):
    model = get_embedding_model()
    result = model.embed(text)
    return result

def should_skip_path(path: str) -> bool:
    """Check if a path should be ignored based on IGNORE_DIRS."""
    path_parts = Path(path).parts
    return any(ignored in path_parts for ignored in config.IGNORE_DIRS)

def process_document(file_path: str, source_name: str = "unknown"):
    """Process a single document and return chunks with embeddings."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        content = load_pdf(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    filename = os.path.basename(file_path)
    chunks = chunk_text(content)

    records = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        records.append({
            "chunk_id": f"{source_name}_{filename}_{i}",
            "filename": filename,
            "source": source_name,
            "chunk_index": i,
            "text": chunk,
            "embedding": embedding
        })

    return records

def ingest_documents():
    logger.info("Starting multi-source ingestion")
    
    db = get_db()
    table_name = "documents"

    if table_name in db.table_names():
        db.drop_table(table_name)
        logger.info("Dropped existing table")

    all_records = []
    total_files = 0
    
    for source in config.KNOWLEDGE_SOURCES:
        source_path = source["path"]
        source_name = source["name"]
        
        logger.info(f"Scanning source: {source_name} at {source_path}")
        
        if not os.path.exists(source_path):
            logger.warning(f"Source path does not exist: {source_path}")
            continue
        
        # Find all indexable files
        source_files = []
        for ext in config.INDEXABLE_EXTENSIONS:
            found = glob.glob(os.path.join(source_path, "**/*" + ext), recursive=True)
            # Filter out ignored directories
            found = [f for f in found if not should_skip_path(f)]
            source_files.extend(found)
        
        logger.info(f"Found {len(source_files)} files in {source_name}")
        
        for file_path in source_files:
            try:
                logger.info(f"Processing: {file_path}")
                records = process_document(file_path, source_name)
                all_records.extend(records)
                total_files += 1
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

    # Create table with data (LanceDB infers schema automatically)
    if all_records:
        table = db.create_table(table_name, data=all_records)
        logger.info(f"Indexed {len(all_records)} chunks from {total_files} files")
    else:
        logger.info("No files to index")

    return {"status": "success", "files_processed": total_files, "chunks_indexed": len(all_records)}
import os

MEMORY_PATH = os.path.expanduser("~/memory")
DOCUMENTS_PATH = os.path.join(MEMORY_PATH, "documents")
INDEX_PATH = os.path.join(MEMORY_PATH, "_index")

MODELS_PATH = os.path.expanduser("~/models")
EMBEDDING_MODEL_PATH = os.path.join(MODELS_PATH, "Qwen3-Embedding-0.6B-f16.gguf")

# Triple model configuration for switching
LLM_MODEL_TECHNICAL = os.path.join(MODELS_PATH, "Qwen3.5-2B.Q4_K_M.gguf")
LLM_MODEL_CONVERSATIONAL = os.path.join(MODELS_PATH, "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
LLM_MODEL_COMPLEX = os.path.join(MODELS_PATH, "gemma-3-4b-it-Q4_K_M.gguf")
LLM_MODEL_PATH = LLM_MODEL_TECHNICAL  # Default

EMBEDDING_N_CTX = 512
LLM_N_CTX = 2048
LLM_N_THREADS = 2

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

TOP_K = 5

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# Multiple Knowledge Sources
KNOWLEDGE_SOURCES = [
    {"name": "notes_documents", "path": os.path.join(os.path.expanduser("~/memory/vault/notes"), "documents")},
    {"name": "pixelmart", "path": os.path.join(os.path.expanduser("~/memory/vault/projects"), "pixelmart")},
    {"name": "moneroo-tools", "path": os.path.join(os.path.expanduser("~/memory/vault/projects"), "moneroo-tools")},
    {"name": "daily-bread", "path": os.path.join(os.path.expanduser("~/memory/vault/projects"), "daily-bread")},
    {"name": "zeat", "path": os.path.join(os.path.expanduser("~/memory/vault/projects"), "zeat")},
]

# Folders to ignore during indexing
IGNORE_DIRS = [
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".env", ".next", "dist", "build", ".cache", "vendor",
    ".idea", ".vscode", "target", "bin", "obj"
]

# File extensions to index
INDEXABLE_EXTENSIONS = [".md", ".txt", ".pdf"]
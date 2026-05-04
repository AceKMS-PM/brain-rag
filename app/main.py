from fastapi import FastAPI
from pydantic import BaseModel
from app import ingest, search, llm, webui, websearch
import re
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Service", description="Local RAG with GGUF models")

# Enable custom web UI
webui.setup_webui(app)

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    web_search: bool = False
    model: str = "auto"  # auto, llama, gemma, qwen

class QueryResponse(BaseModel):
    question: str
    answer: str
    reasoning: str = ""
    sources: list

def is_technical_question(question: str) -> bool:
    technical_keywords = [
        "code", "program", "function", "class", "api", "docker", "git",
        "sql", "python", "javascript", "typescript", "java", "rust",
        "comment", "créer", "implémenter", "développer", "écrire",
        "algorithm", "configuration", "installation", "déployer",
        "debug", "error", "bug", "fix", "optimiser", "comment faire",
        "explain", "tutoriel", "cours", "apprendre"
    ]
    q_lower = question.lower()
    return any(kw in q_lower for kw in technical_keywords)

def is_conversational_question(question: str) -> bool:
    conversational_patterns = [
        r"^(how are you|how('s| is) .*(going|doing|life))",
        r"^(what's up|whats up|wassup)",
        r"^(bonjour|salut|hello|hi|hey)",
        r"^(merci|thanks|thank you)",
        r"^(ok|okay|cool|nice|great|good)",
        r"^(me too|same here|agreed)",
        r"^(tu vas|ça va|comment ça va)",
        r"^(.{1,20})$",  # Very short questions like "ok" or "yes"
    ]
    import re
    q_clean = question.strip().lower()
    for pattern in conversational_patterns:
        if re.match(pattern, q_clean):
            return True
    # Also check for very short questions
    if len(q_clean.split()) <= 3 and not is_technical_question(question):
        return True
    return False

CONVERSATIONAL_RESPONSES = {
    "greeting": [
        "Bonjour! Je suis ravi de vous parler. Comment puis-je vous aider?",
        "Salut! Bienvenue sur votre Second Brain. Une question en particulier?",
        "Hello! Je suis là pour vous aider avec vos documents ou projets.",
    ],
    "how_are_you": [
        "Je vais très bien, merci! Et vous?",
        "Je suis en forme et prêt à vous aider. Et vous?",
    ],
    "thanks": [
        "De rien! Je suis là pour ça.",
        "Avec plaisir! N'hésitez pas si vous avez d'autres questions.",
        "Pas de souci! Ravi d'avoir pu aider.",
    ],
    "me_too": [
        "Super alors! 😊",
        "Parfait, on est sur la même longueur d'onde!",
        "Excellent! anything else?",
    ],
    "short": [
        "Absolument!",
        "D'accord!",
        "Compris!",
        "Parfait!",
    ],
    "goodbye": [
        "Au revoir! Bonne journée!",
        "À bientôt! N'hésitez pas à revenir.",
        "Salut! À la prochaine!",
    ],
}

@app.get("/")
def root():
    return {"status": "running", "service": "RAG Service"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/models")
def list_models():
    return {
        "available_models": [
            {"id": "llama", "name": "Llama 3.2-1B", "description": "Rapide, léger - bon pour tutto"},
            {"id": "qwen", "name": "Qwen 3.5-2B", "description": "Équilibré - bon pour tutto"},
            {"id": "gemma", "name": "Gemma 3-4B", "description": "Plus puissant - pour tâches complexes"}
        ]
    }

@app.post("/ingest")
def ingest_documents():
    return ingest.ingest_documents()

def clean_context(text: str) -> str:
    import re
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()
    return text

@app.post("/query")
def query(request: QueryRequest):
    import random
    
    # Fast path for obvious conversational phrases (before calling LLM)
    q_lower = request.question.lower().strip()
    conversational_triggers = [
        "comment tu vas", "comment ça va", "ça va", "tu vas bien",
        "salut", "bonjour", "hello", "hi", "hey", "coucou",
        "merci", "thanks", "thank", "goodbye", "au revoir"
    ]
    
    is_obviously_conversational = any(t in q_lower for t in conversational_triggers) and len(q_lower.split()) <= 6
    
    if is_obviously_conversational:
        if any(w in q_lower for w in ["bonjour", "salut", "hello", "hi", "hey", "coucou"]):
            response = random.choice(CONVERSATIONAL_RESPONSES["greeting"])
        elif "comment" in q_lower and "va" in q_lower:
            response = random.choice(CONVERSATIONAL_RESPONSES["how_are_you"])
        elif any(w in q_lower for w in ["merci", "thanks", "thank"]):
            response = random.choice(CONVERSATIONAL_RESPONSES["thanks"])
        elif any(w in q_lower for w in ["bye", "au revoir"]):
            response = random.choice(CONVERSATIONAL_RESPONSES["goodbye"])
        else:
            response = "Je comprends! Voulez-vous que je vous aide?"
        
        return {
            "question": request.question,
            "answer": response,
            "reasoning": "Question conversationnelle - détection rapide",
            "sources": []
        }
    
    # Select model - all can handle all tasks
    model_map = {"llama": "conversational", "qwen": "technical", "gemma": "complex"}
    model_type = model_map.get(request.model, "technical")
    model = llm.get_llm_model(model_type)
    logger.info(f"Using model: {request.model} ({model_type})")
    
    # Simple conversational check (no intent routing)
    q_clean = request.question.lower().strip()
    if any(w in q_clean for w in ["bonjour", "salut", "hello", "hi", "hey", "coucou"]):
        # Use simple conversational handling
        q_clean = request.question.lower().strip()
        if any(w in q_clean for w in ["bonjour", "salut", "hello", "hi", "hey"]):
            response = random.choice(CONVERSATIONAL_RESPONSES["greeting"])
        elif "how are" in q_clean or "ça va" in q_clean or "tu vas" in q_clean or "comment vas" in q_clean:
            response = random.choice(CONVERSATIONAL_RESPONSES["how_are_you"])
        elif any(w in q_clean for w in ["merci", "thanks", "thank"]):
            response = random.choice(CONVERSATIONAL_RESPONSES["thanks"])
        else:
            response = "Je comprends! Voulez-vous que je vous aide avec quelque chose?"
        
        return {
            "question": request.question,
            "answer": response,
            "reasoning": f"Intent détecté: CONVERSATIONAL - Pas de recherche dans les documents.",
            "sources": []
        }
    
    # Normal RAG flow for TECHNICAL/COMPLEX/UNKNOWN
    search_result = search.search(request.question, request.top_k)
    if "error" in search_result:
        return {"error": search_result["error"]}

    context_parts = [clean_context(r["text"]) for r in search_result["results"]]
    
    web_results = []
    if request.web_search:
        web_results = websearch.search_web(request.question)
        if web_results:
            web_context = "\n\n--- Recherche Web ---\n"
            for r in web_results:
                web_context += f"Source: {r['title']}\nURL: {r['url']}\n{r['content']}\n\n"
            context_parts.append(web_context)

    context = "\n\n".join(context_parts)

    answer = llm.generate_answer(context, request.question, model_type)

    # Extract reasoning section if present (handle Qwen3.5 thinking)
    reasoning = ""
    
    # Handle Qwen3.5 <think> blocks
    if "<think>" in answer:
        think_parts = answer.split("</think>")
        if len(think_parts) > 1:
            thinking = think_parts[0].replace("<think>", "").strip()
            if thinking:
                reasoning = thinking
            answer = think_parts[1].strip()
    
    # Handle ## Raisonnement section
    if "## Raisonnement" in answer:
        parts = answer.split("## Raisonnement")
        if len(parts) > 1:
            reasoning_part = parts[1].split("##")[0] if "##" in parts[1] else parts[1]
            reasoning = reasoning_part.strip()
            # Keep only the answer part (without reasoning)
            answer = parts[0].replace("## Réponse", "").strip()
            # Only include code if question is technical
            if is_technical_question(request.question) and "## Code" in parts[1]:
                code_part = "## Code" + parts[1].split("## Code")[1]
                answer += "\n" + code_part

    sources = []
    for r in search_result["results"]:
        sources.append({
            "filename": r["filename"],
            "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"]
        })
    
    if web_results:
        for r in web_results:
            sources.append({
                "filename": "🌐 " + r["title"],
                "text": r["url"]
            })

    model_names = {"technical": "Qwen 3.5-2B", "conversational": "Llama 3.2-1B", "complex": "Gemma 3-4B"}
    
    return {
        "question": request.question,
        "answer": answer,
        "reasoning": reasoning,
        "sources": sources,
        "model": model_names.get(model_type, request.model)
    }


# ============================================
# OpenAI Compatible API Endpoints
# ============================================

class OpenAIMessage(BaseModel):
    role: str
    content: str

class OpenAIChatCompletionRequest(BaseModel):
    model: str
    messages: list[OpenAIMessage]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False

class OpenAIChatCompletionChoice(BaseModel):
    index: int
    message: OpenAIMessage
    finish_reason: str = "stop"

class OpenAIChatCompletion(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[OpenAIChatCompletionChoice]

@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatCompletionRequest):
    """OpenAI-compatible endpoint for OpenCode integration"""
    import time
    import uuid
    
    # Extract user message
    user_message = None
    for msg in request.messages:
        if msg.role == "user":
            user_message = msg.content
            break
    
    if not user_message:
        return {"error": "No user message found"}
    
    # Map model name to intent
    model_map = {
        "llama": "CONVERSATIONAL",
        "gemma": "COMPLEX",
        "qwen": "TECHNICAL",
        "auto": "auto"
    }
    
    requested_model = request.model.lower() if request.model else "auto"
    # Handle provider/model format (e.g., "local-brain/llama" -> "llama")
    if "/" in requested_model:
        requested_model = requested_model.split("/")[-1]
    intent = model_map.get(requested_model, "auto")
    logger.info(f"Parsed model: {requested_model} -> intent: {intent}")
    
    logger.info(f"OpenAI request - model: {request.model}, intent: {intent}")
    
    # Run RAG flow
    search_result = search.search(user_message, 5)
    
    if "error" in search_result:
        return {"error": search_result["error"]}
    
    context_parts = [clean_context(r["text"]) for r in search_result["results"]]
    context = "\n\n".join(context_parts)
    
    # Generate answer with appropriate model
    answer = llm.generate_answer(context, user_message, intent if intent != "auto" else "TECHNICAL")
    
    # Extract content from answer (remove reasoning section if present)
    final_content = answer
    if "## Raisonnement" in answer:
        final_content = answer.split("## Raisonnement")[0].replace("## Réponse", "").strip()
    
    # Build OpenAI response with all required fields
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": final_content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(final_content.split()),
            "total_tokens": len(user_message.split()) + len(final_content.split())
        }
    }


@app.get("/v1/models")
async def list_openai_models():
    """List available models in OpenAI format"""
    return {
        "object": "list",
        "data": [
            {
                "id": "auto",
                "object": "model",
                "created": 1700000000,
                "owned_by": "local-brain"
            },
            {
                "id": "llama",
                "object": "model",
                "created": 1700000000,
                "owned_by": "local-brain"
            },
            {
                "id": "gemma",
                "object": "model",
                "created": 1700000000,
                "owned_by": "local-brain"
            },
            {
                "id": "qwen",
                "object": "model",
                "created": 1700000000,
                "owned_by": "local-brain"
            }
        ]
    }
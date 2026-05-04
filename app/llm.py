import logging
from llama_cpp import Llama
from app import config

logger = logging.getLogger(__name__)

llm_technical = None
llm_conversational = None
llm_complex = None

def get_llm_model(model_type: str = "technical"):
    """Load and cache models based on type."""
    global llm_technical, llm_conversational, llm_complex
    
    if model_type == "conversational":
        if llm_conversational is None:
            logger.info(f"Loading conversational model from {config.LLM_MODEL_CONVERSATIONAL}")
            llm_conversational = Llama(
                model_path=config.LLM_MODEL_CONVERSATIONAL,
                n_ctx=config.LLM_N_CTX,
                n_threads=config.LLM_N_THREADS,
                n_gpu_layers=0,
                flash_attn=False
            )
            logger.info("Conversational model loaded")
        return llm_conversational
    elif model_type == "complex":
        if llm_complex is None:
            logger.info(f"Loading complex model from {config.LLM_MODEL_COMPLEX}")
            llm_complex = Llama(
                model_path=config.LLM_MODEL_COMPLEX,
                n_ctx=config.LLM_N_CTX,
                n_threads=config.LLM_N_THREADS,
                n_gpu_layers=0,
                flash_attn=False
            )
            logger.info("Complex model loaded")
        return llm_complex
    else:
        if llm_technical is None:
            logger.info(f"Loading technical model from {config.LLM_MODEL_TECHNICAL}")
            llm_technical = Llama(
                model_path=config.LLM_MODEL_TECHNICAL,
                n_ctx=config.LLM_N_CTX,
                n_threads=config.LLM_N_THREADS,
                n_gpu_layers=0,
                flash_attn=False
            )
            logger.info("Technical model loaded")
        return llm_technical

def get_model_for_intent(intent: str):
    """Select appropriate model based on intent."""
    if intent == "CONVERSATIONAL":
        return get_llm_model("conversational")
    elif intent == "COMPLEX":
        return get_llm_model("complex")
    return get_llm_model("technical")
    if intent == "CONVERSATIONAL":
        return get_llm_model("conversational")
    return get_llm_model("technical")

def analyze_intent(question: str) -> str:
    """Determines the user's intent to route the response strategy."""
    model = get_llm_model("technical")
    
    q = question.strip().lower()
    
    # Fast path for obvious greetings
    conversational_fast = ["hey", "hi", "hello", "salut", "bonjour", "hey qwen", "hi qwen", "hello qwen",
                          "ça va", "comment ça va", "tu vas", "merci", "thanks"]
    if any(q == w or q.startswith(w + " ") for w in conversational_fast):
        return "CONVERSATIONAL"
    
    # For short questions, also check conversational patterns
    if len(q.split()) <= 3:
        if any(w in q for w in ["ça va", "tu vas", "comment vas", "merci", "thanks", "ok", "good"]):
            return "CONVERSATIONAL"
    
    prompt = f"""<|im_start|>system
Tu analyzes l'intention de cette question. Réponds EXACTEMENT par un seul mot sans autre texte.

Règles strictes:
- CONVERSATIONAL: Salutations (bonjour, salut, hey), compliments, questions sur toi, trivialités, messages courts (<5 mots) qui ne sont pas techniques.
- TECHNICAL: Questions sur du code, programmation, outils, configuration, bugs, APIs, requêtes avec mots techniques (comment, pourquoi, créer, implémenter).
- COMPLEX: Demandes d'analyse, comparaison, plan, architecture, plusieurs options.
- UNKNOWN: Trop ambigu pour classer.

Examples:
- "salut" -> CONVERSATIONAL
- "comment ça va" -> CONVERSATIONAL  
- "c'est quoi eslint" -> TECHNICAL
- "comment créer un cron" -> TECHNICAL
- "explique moi les differences entre docker et kubernetes" -> COMPLEX
<|im_end|>
<|im_start|>user
Question: {question}
<|im_end|>
<|im_start|>assistant
"""
    
    response = model(
        prompt,
        max_tokens=10,
        temperature=0
    )
    return response["choices"][0]["text"].strip().upper()

def generate_answer(context: str, question: str, intent: str = "TECHNICAL") -> str:
    # Use appropriate model based on intent
    model = get_model_for_intent(intent)
    is_conversational = intent == "CONVERSATIONAL"
    
    # Customize system prompt based on intent
    if is_conversational:
        system_prompt = "Tu es un compagnon intelligent, chaleureux et naturel. Réponds de façon concise et empathique. Une seule réponse, pas de répétition."
        max_tokens = 256
    else:
        system_prompt = "Tu es un assistant technique expert. Réponds en détail avec précision en utilisant le contexte. Utilise des blocs de code si nécessaire. Sois exhaustif."
        max_tokens = 2048

    # Use correct template based on which model is loaded
    # We can detect by checking the loaded model file path
    model_path = model.model_path if hasattr(model, 'model_path') else ""
    
    if "Llama" in model_path:
        # Llama 3.2 format with context
        prompt = f"""<|start_header_id|>system<|end_header_id|>

{system_prompt}

Contexte:
{context[:1500]}

Question: {question}<|eot_id|>
<|start_header_id|>user<|end_header_id|>

?<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
        stop_seqs = ["<|eot_id|>", "<|start_header_id|>user"]
    elif "gemma" in model_path.lower():
        # Gemma 3 format with context
        prompt = f"""<start_of_turn>system
{system_prompt}
Contexte:
{context[:4000]}
<end_of_turn>
<start_of_turn>user
{question}<end_of_turn>
<start_of_turn>model
"""
        stop_seqs = ["<end_of_turn>", "<start_of_turn>user"]
    else:
        # Qwen 3 format (default)
        prompt = f"""<|im_start|>system
{system_prompt}

INSTRUCTIONS:
1. Raisonnement: Explique brièvement ton approche.
2. Code: Utilise ```langage ... ``` si requis.
3. Sources: Cite les sources du contexte.
4. Si insuffisant: Dis-le honnêtement.

FORMAT DE RÉPONSE:
## Réponse
[Ta réponse]

## Raisonnement
[Ton raisonnement]

## Code (si applicable)
```langage
code
```

## Sources
- [source]
<|im_end|>
<|im_start|>user
Contexte:
{context[:1500]}

Question: {question}
<|im_end|>
<|im_start|>assistant
"""
        stop_seqs = ["Question:", "Contexte:", "## Sources"]
    
    response = model(
        prompt,
        max_tokens=max_tokens,
        temperature=0.3,
        stop=stop_seqs
    )

    return response["choices"][0]["text"].strip()
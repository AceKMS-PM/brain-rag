# LLM Layer

## Overview (`app/llm.py`)

Manages three local GGUF models via `llama-cpp-python` for text generation.

## Models

| Type | Model | Size | Use Case |
|------|-------|------|----------|
| **Technical** | Qwen3.5-2B Q4_K_M | ~1.5GB | Code, config, tutorials |
| **Conversational** | Llama-3.2-1B Q4_K_M | ~1GB | Greetings, chat |
| **Complex** | Gemma-3-4b Q4_K_M | ~2.5GB | Analysis, architecture |

All models run on CPU with 2 threads, 2048 context window.

## Model Loading

Models are lazy-loaded and cached as module-level singletons:

```python
llm_technical = None   # Loaded on first technical request
llm_conversational = None   # Loaded on first conversational request
llm_complex = None   # Loaded on first complex request
```

## Prompt Templates

Each model uses its own chat format:

### Llama 3.2
```
<|start_header_id|>system<|end_header_id|>
{system_prompt}
Contexte: {context[:1500]}
Question: {question}<|eot_id|>
<|start_header_id|>user<|end_header_id|>
?<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
```

### Gemma 3
```
<start_of_turn>system
{system_prompt}
Contexte: {context[:4000]}
<end_of_turn>
<start_of_turn>user
{question}<end_of_turn>
<start_of_turn>model
```

### Qwen 3 (default)
```
<think>
{system_prompt}
Contexte: {context[:1500]}
Question: {question}
</think>
```

## Generation Parameters

| Intent | Temperature | Max Tokens | System Prompt |
|--------|-------------|------------|---------------|
| Conversational | 0.3 | 256 | "Warm, concise, empathetic" |
| Technical/Complex | 0.3 | 2048 | "Expert, detailed, precise" |

## Key Functions

| Function | Purpose |
|----------|---------|
| `get_llm_model(type)` | Load/cache model by type |
| `get_model_for_intent(intent)` | Map intent to model |
| `generate_answer(context, question, intent)` | Generate response |

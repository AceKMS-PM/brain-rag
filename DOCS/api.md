# API Reference

## Overview (`app/main.py`)

FastAPI application serving the RAG backend with two API styles.

## Standard Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Service status |
| GET | `/health` | Health check |
| GET | `/models` | List available LLMs |
| POST | `/ingest` | Trigger document ingestion |
| POST | `/query` | Ask a question |

### `/query` Request

```json
{
  "question": "how to use git rebase?",
  "top_k": 5,
  "web_search": false,
  "model": "qwen"
}
```

**Model options**: `llama`, `qwen`, `gemma`

### `/query` Response

```json
{
  "question": "...",
  "answer": "...",
  "reasoning": "...",
  "sources": [
    {"filename": "git.md", "text": "..."}
  ],
  "model": "Qwen 3.5-2B"
}
```

## OpenAI-Compatible Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/v1/models` | List models (OpenAI format) |
| POST | `/v1/chat/completions` | Chat completion |

### `/v1/chat/completions` Request

```json
{
  "model": "qwen",
  "messages": [
    {"role": "user", "content": "What is git rebase?"}
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

### `/v1/chat/completions` Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "qwen",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Git rebase is..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 42,
    "total_tokens": 47
  }
}
```

## Response Pipeline

1. Conversational phrase detection (fast path)
2. Model selection based on request.model
3. Hybrid search for relevant context
4. Web search (if enabled)
5. LLM generates answer
6. Reasoning extraction (<think> tags)
7. Response assembly

# Brain RAG - Agent Instructions

## Project Overview
Local Second Brain RAG system with FastAPI + LanceDB + GGUF models + Tauri desktop UI.

## Current Tasks

### High Priority
- [ ] Resolve CORS issues between Tauri and FastAPI
- [ ] Optimize model loading to prevent OOM crashes on 4GB RAM
- [ ] Implement unified lifecycle management (backend management within Rust process)

### Medium Priority
- [ ] Implement unified lifecycle management (backend from Rust process)

## Commands

| Command | Description |
|---------|-------------|
| `./brain-ai start` | Start RAG service |
| `./brain-ai stop` | Stop RAG service |
| `./brain-ai status` | Check status |
| `./brain-ai logs` | View logs |

## Available Skills
- `security-review` - Security audits
- `rust-code-review` - Rust/Tauri code review
- `smart-review` - General architecture review
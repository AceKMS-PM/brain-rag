# UI & Desktop App

## Web UI (`templates/index.html`)

Single-page application with vanilla HTML/CSS/JS.

### Features
- Chat-style interface
- Markdown rendering
- Code block copy buttons
- Conversation history (localStorage)
- Model selector (Llama, Qwen, Gemma)
- Web search toggle
- Dark navy theme (`#050a18`) with violet accents (`#d0bcff`)

### Communication
- Calls FastAPI `/query` endpoint
- Calls `/models` for available models
- Calls `/ingest` for reindexing

## WebUI Setup (`app/webui.py`)

Mounts static files and serves `index.html` at the root path.

## Tauri Desktop (`src-tauri/`)

Wraps the web UI in a native desktop application.

### Structure
```
src-tauri/
├── Cargo.toml          # Rust dependencies
├── build.rs            # Tauri build script
├── tauri.conf.json     # App configuration
├── capabilities/
│   └── default.json    # Permission config
├── icons/
│   └── icon.png        # App icon
├── gen/                # Auto-generated (gitignored)
└── src/
    └── main.rs         # Rust entry point
```

### Configuration
- **Window**: 1200x800, resizable
- **Frontend**: `../templates/` (relative to src-tauri/)
- **Identifier**: `com.brain.rag`

### Commands

```bash
# Development (requires FastAPI running on port 3000)
npm run tauri:dev

# Production build
npm run tauri:build
```

### Current State
- Shell is built and compiles
- Needs system deps: `libgtk-3-dev`, `libwebkit2gtk-4.1-dev`
- Runs locally with `cargo run --manifest-path src-tauri/Cargo.toml`

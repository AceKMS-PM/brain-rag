from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

def setup_webui(app: FastAPI):
    template_path = Path(__file__).parent.parent / "templates" / "index.html"
    html_content = template_path.read_text()

    @app.get("/", response_class=HTMLResponse)
    async def home():
        return html_content

    @app.get("/stats")
    async def stats():
        from app.ingest import get_db
        db = get_db()
        if "documents" in db.table_names():
            table = db.open_table("documents")
            return {"chunks": table.count_rows()}
        return {"chunks": 0}
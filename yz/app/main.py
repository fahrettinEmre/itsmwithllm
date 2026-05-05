from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import httpx
from pathlib import Path

from app.agent import run_rca_pipeline
from app.config import OLLAMA_BASE_URL
from app.itsm_connector import get_ticket_or_raise, list_tickets
from app.ollama_support import OLLAMA_HINT_TR, ollama_unreachable
from app.rag_store import refresh_vectorstore
from app.ui_api import router as ui_router

app = FastAPI(title="ITSM RAG RCA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ui_router)

_static_ui = Path(__file__).resolve().parent / "static_ui"
if _static_ui.is_dir() and (_static_ui / "index.html").is_file():
    app.mount("/ui", StaticFiles(directory=str(_static_ui), html=True), name="ui")


class AnalyzeTextBody(BaseModel):
    text: str = Field(..., min_length=3, max_length=8000)
    title: str | None = None
    priority: str | None = None


def _ollama_503(exc: BaseException) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "error": "ollama_unreachable",
            "message": str(exc),
            "hint": OLLAMA_HINT_TR,
            "ollama_url": OLLAMA_BASE_URL,
        },
    )


async def _run_rca_with_ollama_errors(ticket):
    try:
        return await run_rca_pipeline(ticket)
    except Exception as e:
        if ollama_unreachable(e):
            raise _ollama_503(e) from e
        raise


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/ollama")
async def health_ollama():
    """Ollama API ayakta mı (embedding/LLM öncesi kontrol)."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url)
            r.raise_for_status()
    except Exception as e:
        return {"ollama": "down", "url": OLLAMA_BASE_URL, "detail": str(e)}
    return {"ollama": "up", "url": OLLAMA_BASE_URL}


@app.get("/tickets")
async def tickets():
    """Mock ITSM listesi (MCP list_tickets eşleniği)."""
    return {"tickets": list_tickets()}


@app.post("/analyze/ticket/{ticket_id}")
async def analyze_ticket_id(ticket_id: int):
    try:
        ticket = get_ticket_or_raise(ticket_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return await _run_rca_with_ollama_errors(ticket)


@app.post("/analyze/text")
async def analyze_text(body: AnalyzeTextBody):
    from app.itsm_connector import Ticket

    t = Ticket(id=0, text=body.text.strip(), title=body.title, priority=body.priority)
    return await _run_rca_with_ollama_errors(t)


@app.post("/admin/reindex")
async def reindex():
    try:
        refresh_vectorstore()
    except Exception as e:
        if ollama_unreachable(e):
            raise _ollama_503(e) from e
        raise
    return {"ok": True, "message": "Vector store rebuilt from knowledge/."}


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Arayuz varsa /ui/ adresine yonlendir."""
    from fastapi.responses import RedirectResponse

    ui = Path(__file__).resolve().parent / "static_ui"
    if ui.is_dir() and (ui / "index.html").is_file():
        return RedirectResponse(url="/ui/")
    return {"docs": "/docs", "hint": "Arayuz icin: cd frontend && npm run build"}

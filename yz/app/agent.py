"""Agent: sınıflandırma → RAG → offline LLM ile RCA."""

import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, RAG_TOP_K
from app.itsm_connector import Ticket
from app.rag_store import get_vectorstore


def classify_ticket(text: str) -> str:
    """Hafif çok adımlı akış: anahtar kelime ile problem sınıfı."""
    t = text.lower()
    if any(w in t for w in ("timeout", "connection pool", "database", "db ")):
        return "database"
    if any(w in t for w in ("cpu", "memory", "spike", "load")):
        return "performance"
    if any(w in t for w in ("latency", "slow", "network", "remote")):
        return "network"
    if any(w in t for w in ("503", "502", "http", "api", "service unavailable")):
        return "availability"
    if any(w in t for w in ("disk", "full", "space", "partition")):
        return "storage"
    return "general"


def _format_context(docs: list) -> str:
    parts = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "?")
        parts.append(f"[{i}] ({src})\n{d.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


async def ollama_generate(prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    async with httpx.AsyncClient(timeout=180.0) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    return (data.get("response") or "").strip()


def build_rca_prompt(ticket: Ticket, category: str, context: str) -> str:
    return f"""You are an IT operations expert. Produce a concise Root Cause Analysis in English.

Ticket ID: {ticket.id}
Title: {ticket.title or "N/A"}
Priority: {ticket.priority or "N/A"}
Description: {ticket.text}

Problem category (heuristic): {category}

Knowledge snippets (retrieved):
{context}

Output EXACTLY in this structure (use these headings):

Root Cause:
<one or two sentences>

Reason:
<short explanation>

Solution:
<actionable steps, bullet lines with - if needed>

If context is thin, still give best-effort RCA and note assumptions briefly under Reason.
"""


async def run_rca_pipeline(ticket: Ticket) -> dict:
    category = classify_ticket(ticket.text)
    vs = get_vectorstore()
    query = f"{category}: {ticket.text}"
    docs = vs.similarity_search(query, k=RAG_TOP_K)
    context = _format_context(docs)
    prompt = build_rca_prompt(ticket, category, context)
    rca_text = await ollama_generate(prompt)
    return {
        "ticket_id": ticket.id,
        "category": category,
        "rag_sources": [d.metadata.get("source") for d in docs],
        "rca_markdown": rca_text,
    }

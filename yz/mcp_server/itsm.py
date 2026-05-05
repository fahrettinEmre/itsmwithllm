"""ITSM araçları: mock bilet listesi ve tekil kayıt (MCP tools)."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from app.itsm_connector import get_ticket, list_tickets

mcp = FastMCP(
    "itsm-mock",
    instructions=(
        "Mock ITSM bağlayıcısı. Biletleri listelemek için itsm_list_tickets, "
        "tam metin için itsm_get_ticket kullanın. Üretimde aynı araçlar ServiceNow/Jira API arkasına bağlanır."
    ),
)


@mcp.tool()
def itsm_list_tickets() -> list[dict[str, Any]]:
    """Açık mock biletlerin özet listesi (id, title, priority, kısa preview)."""
    return list_tickets()


@mcp.tool()
def itsm_get_ticket(ticket_id: int) -> dict[str, Any]:
    """Verilen id için bilet tam metnini döndürür; yoksa not_found."""
    t = get_ticket(ticket_id)
    if t is None:
        return {"error": "not_found", "ticket_id": ticket_id}
    return {
        "id": t.id,
        "title": t.title,
        "priority": t.priority,
        "text": t.text,
    }

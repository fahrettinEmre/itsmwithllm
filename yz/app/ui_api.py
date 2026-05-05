"""Web UI icin API: MCP koprusu + sohbet yorumu."""

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.mcp_bridge import mcp_call_tool

router = APIRouter(prefix="/api", tags=["ui"])


@router.get("/mcp/tickets")
async def api_mcp_list_tickets():
    """MCP araci itsm_list_tickets."""
    try:
        rows = await mcp_call_tool("itsm_list_tickets", {})
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "mcp_failed", "message": str(e)},
        ) from e
    return {"source": "mcp", "tool": "itsm_list_tickets", "tickets": rows}


@router.get("/mcp/tickets/{ticket_id}")
async def api_mcp_get_ticket(ticket_id: int):
    """MCP araci itsm_get_ticket."""
    try:
        parts = await mcp_call_tool("itsm_get_ticket", {"ticket_id": ticket_id})
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "mcp_failed", "message": str(e)},
        ) from e
    if not parts:
        raise HTTPException(status_code=502, detail="MCP bos yanit")
    body = parts[0]
    if body.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=body)
    return {"source": "mcp", "tool": "itsm_get_ticket", "ticket": body}


class ChatBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


def _extract_ticket_id(message: str) -> int | None:
    """Tek bilet istegi: 2 numarali, #2, ticket 2, bilet 2, id 2."""
    m = message.strip()
    patterns = (
        r"(\d+)\s*numaral[ıi]",
        r"#\s*(\d+)",
        r"\b(?:ticket|bilet)\s*[#:]?\s*(\d+)\b",
        r"\bid\s*:?\s*(\d+)\b",
    )
    for pat in patterns:
        mm = re.search(pat, m, re.IGNORECASE)
        if mm:
            try:
                return int(mm.group(1))
            except ValueError:
                continue
    return None


def _wants_list_all(message: str) -> bool:
    """Tum listeyi isteme (altstring 'liste' ile 'listele' karismasin)."""
    m = message.strip().lower()
    if re.search(r"\b(listele|list\s|listing)\b", m):
        return True
    if re.search(r"\b(tüm|tum)\s+.{0,24}?(ticket|bilet)", m):
        return True
    if re.search(r"(biletleri|ticketları|ticketlari|tickets?)\s+(list|göster|goster|getir)", m):
        return True
    if re.search(r"\b(all|show)\s+(tickets?|bilet)", m):
        return True
    return False


@router.post("/chat")
async def api_chat(body: ChatBody):
    """Sohbet: tekil bilet (itsm_get_ticket) veya liste (itsm_list_tickets)."""
    raw = body.message.strip()
    m = raw.lower()
    tid = _extract_ticket_id(raw)
    list_all = _wants_list_all(raw)

    if list_all:
        try:
            tickets = await mcp_call_tool("itsm_list_tickets", {})
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail={"error": "mcp_failed", "message": str(e)},
            ) from e
        return {
            "intent": "list_tickets",
            "reply": f"MCP (itsm_list_tickets) ile {len(tickets)} kayit alindi.",
            "ticket": None,
            "tickets": tickets,
        }

    if tid is not None:
        try:
            parts = await mcp_call_tool("itsm_get_ticket", {"ticket_id": tid})
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail={"error": "mcp_failed", "message": str(e)},
            ) from e
        if not parts:
            raise HTTPException(status_code=502, detail="MCP bos yanit")
        ticket = parts[0]
        if ticket.get("error") == "not_found":
            return {
                "intent": "get_ticket",
                "reply": f"MCP (itsm_get_ticket): #{tid} bulunamadi.",
                "ticket": None,
                "tickets": None,
            }
        extra = (
            " — sagda RCA icin hazir."
            if re.search(r"(getir|göster|goster|numaral|#|detay)", m, re.I)
            else ""
        )
        return {
            "intent": "get_ticket",
            "reply": f"MCP **itsm_get_ticket({tid})**: **{ticket.get('title') or '—'}**{extra}",
            "ticket": ticket,
            "tickets": None,
        }

    return {
        "intent": "unknown",
        "reply": "Ornekler: **biletleri listele**, **2 numarali ticketi getir**, **#3**, **ticket 2**.",
        "ticket": None,
        "tickets": None,
    }

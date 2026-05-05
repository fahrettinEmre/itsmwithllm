"""
Mock ITSM veri katmanı. Üretimde ServiceNow/Jira MCP araçları bu arayüzün arkasına bağlanır.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Ticket:
    id: int
    text: str
    title: str | None = None
    priority: str | None = None


_MOCK_TICKETS: list[Ticket] = [
    Ticket(1, "Production API returns 503 intermittently during peak hours", "API 503", "P1"),
    Ticket(2, "Database connection timeout from payment service", "DB timeout", "P1"),
    Ticket(3, "CPU spike on app servers after last deploy", "CPU spike", "P2"),
    Ticket(4, "Users report slow page loads from remote offices", "Network latency", "P3"),
    Ticket(5, "Disk full on log partition, service restarts", "Disk full", "P2"),
]


def list_tickets() -> list[dict[str, Any]]:
    """MCP tool: list_tickets benzeri çıktı."""
    return [
        {"id": t.id, "title": t.title, "priority": t.priority, "preview": t.text[:80] + "..."}
        for t in _MOCK_TICKETS
    ]


def get_ticket(ticket_id: int) -> Ticket | None:
    """MCP tool: get_ticket — tek kayıt."""
    for t in _MOCK_TICKETS:
        if t.id == ticket_id:
            return t
    return None


def get_ticket_or_raise(ticket_id: int) -> Ticket:
    t = get_ticket(ticket_id)
    if t is None:
        raise KeyError(f"Ticket {ticket_id} not found")
    return t

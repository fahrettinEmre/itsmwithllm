"""MCP ile bilet cek -> REST ile RCA (RAG + Ollama LLM).

1) stdio MCP: itsm_get_ticket
2) HTTP: POST /analyze/text (text, title, priority)

Oncelikler: proje kokunden calistirin; docker compose ayaktaysa API genelde :8000.
  .venv\\Scripts\\python scripts\\test_mcp_then_rca.py
  .venv\\Scripts\\python scripts\\test_mcp_then_rca.py --base http://127.0.0.1:8000 --ticket-id 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import anyio
import httpx
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]


def _python_exe() -> str:
    win = ROOT / ".venv" / "Scripts" / "python.exe"
    if win.is_file():
        return str(win)
    return sys.executable


async def _mcp_get_ticket(ticket_id: int) -> dict:
    params = StdioServerParameters(
        command=_python_exe(),
        args=["-m", "mcp_server"],
        cwd=str(ROOT),
    )
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        async with stdio_client(params, errlog=devnull) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "itsm_get_ticket",
                    {"ticket_id": ticket_id},
                )
                for block in result.content:
                    if block.type == "text" and block.text.strip():
                        return json.loads(block.text)
    return {}


def main() -> None:
    p = argparse.ArgumentParser(description="MCP bilet -> HTTP RCA")
    p.add_argument(
        "--base",
        default="http://localhost:8000",
        help="FastAPI tabani",
    )
    p.add_argument("--ticket-id", type=int, default=2)
    args = p.parse_args()
    base = args.base.rstrip("/")

    async def _go() -> None:
        ticket = await _mcp_get_ticket(args.ticket_id)
        print("=== 1) MCP itsm_get_ticket ===")
        print(json.dumps(ticket, indent=2, ensure_ascii=False))
        if ticket.get("error") == "not_found":
            raise SystemExit(f"Bilet bulunamadi: {args.ticket_id}")

        payload = {
            "text": ticket.get("text") or "",
            "title": ticket.get("title"),
            "priority": ticket.get("priority"),
        }
        if not payload["text"].strip():
            raise SystemExit("MCP yanitinda text bos")

        print("\n=== 2) HTTP POST /analyze/text (RAG + LLM) ===")
        with httpx.Client(timeout=300.0) as client:
            ho = client.get(f"{base}/health/ollama")
            print("GET /health/ollama:", ho.json())
            r = client.post(f"{base}/analyze/text", json=payload)
            print("status:", r.status_code)
            try:
                body = r.json()
            except Exception:
                print(r.text[:3000])
                raise
            print(json.dumps(body, indent=2, ensure_ascii=False)[:12000])
            if r.is_success and body.get("rca_markdown"):
                print("\n--- rca_markdown (ilk 600 karakter) ---\n")
                print((body["rca_markdown"] or "")[:600])

    anyio.run(_go, backend="asyncio")


if __name__ == "__main__":
    main()

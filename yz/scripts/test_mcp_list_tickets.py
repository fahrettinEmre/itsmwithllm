"""MCP stdio: itsm_list_tickets aracini test eder (sunucuyu alt surec olarak baslatir)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]


def _python_exe() -> str:
    win = ROOT / ".venv" / "Scripts" / "python.exe"
    if win.is_file():
        return str(win)
    return sys.executable


async def _run() -> None:
    params = StdioServerParameters(
        command=_python_exe(),
        args=["-m", "mcp_server"],
        cwd=str(ROOT),
    )
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        async with stdio_client(params, errlog=devnull) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                names = [t.name for t in listed.tools]
                print("list_tools:", names)
                if "itsm_list_tickets" not in names:
                    raise SystemExit("itsm_list_tickets araci yok")
                result = await session.call_tool("itsm_list_tickets", {})
                tickets: list[dict] = []
                for block in result.content:
                    if block.type == "text" and block.text.strip():
                        tickets.append(json.loads(block.text))
                print("itsm_list_tickets (5 kayit):")
                print(json.dumps(tickets, indent=2, ensure_ascii=False))


def main() -> None:
    anyio.run(_run, backend="asyncio")


if __name__ == "__main__":
    main()

"""MCP stdio: itsm_get_ticket ile tekil bilet ceker (varsayilan: id=2)."""

from __future__ import annotations

import argparse
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


async def _run(ticket_id: int) -> None:
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
                parts: list[dict] = []
                for block in result.content:
                    if block.type == "text" and block.text.strip():
                        parts.append(json.loads(block.text))
                if len(parts) == 1:
                    print(json.dumps(parts[0], indent=2, ensure_ascii=False))
                else:
                    print(json.dumps(parts, indent=2, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("ticket_id", nargs="?", type=int, default=2)
    args = p.parse_args()

    async def _main() -> None:
        await _run(args.ticket_id)

    anyio.run(_main, backend="asyncio")


if __name__ == "__main__":
    main()

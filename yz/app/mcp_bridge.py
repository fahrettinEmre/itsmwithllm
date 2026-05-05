"""FastAPI icinden stdio MCP sunucusuna kisa oturum (itsm_* araclari)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]


def python_for_mcp() -> str:
    win = ROOT / ".venv" / "Scripts" / "python.exe"
    if win.is_file():
        return str(win)
    nix = ROOT / ".venv" / "bin" / "python"
    if nix.is_file():
        return str(nix)
    return sys.executable


def mcp_cwd() -> str:
    return str(ROOT)


async def mcp_call_tool(name: str, arguments: dict | None = None) -> list[dict]:
    """MCP tool cagir; metin bloklarini JSON olarak parse edip listeler."""
    arguments = arguments or {}
    params = StdioServerParameters(
        command=python_for_mcp(),
        args=["-m", "mcp_server"],
        cwd=mcp_cwd(),
    )
    out: list[dict] = []
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        async with stdio_client(params, errlog=devnull) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                for block in result.content:
                    if block.type == "text" and block.text.strip():
                        out.append(json.loads(block.text))
    return out

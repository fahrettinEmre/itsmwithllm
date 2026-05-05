"""Çalıştırma: proje kökünden `python -m mcp_server` (stdio, Cursor MCP)."""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from mcp_server.itsm import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")

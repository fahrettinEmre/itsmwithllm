"""RCA HTTP API testi: /analyze/ticket/{id} ve /analyze/text.

MCP kullanmaz; FastAPI + mock itsm_connector ile dogrudan HTTP cagrilir.
MCP akisi icin: scripts/test_mcp_get_ticket.py

Kullanim (uygulama ayaktayken, proje kokunden):
  .venv\\Scripts\\python scripts\\test_rca_http.py
  .venv\\Scripts\\python scripts\\test_rca_http.py http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx


def main() -> None:
    p = argparse.ArgumentParser(description="RCA API smoke test")
    p.add_argument(
        "base",
        nargs="?",
        default="http://localhost:8000",
        help="API tabani (varsayilan http://localhost:8000)",
    )
    args = p.parse_args()
    base = args.base.rstrip("/")

    with httpx.Client(timeout=300.0) as client:
        h = client.get(f"{base}/health")
        h.raise_for_status()
        print("GET /health:", h.json())

        o = client.get(f"{base}/health/ollama")
        print("GET /health/ollama:", o.json())
        if o.json().get("ollama") != "up":
            print(
                "\nUyari: Ollama 'up' degilse asagidaki analyze istekleri 503 verebilir.\n",
                file=sys.stderr,
            )

        # REST: ticket 2 mock listeden FastAPI ile alinir (MCP degil).
        print("\n--- POST /analyze/ticket/2 ---")
        r2 = client.post(f"{base}/analyze/ticket/2")
        print("status:", r2.status_code)
        try:
            body = r2.json()
        except Exception:
            print(r2.text[:2000])
            raise
        print(json.dumps(body, indent=2, ensure_ascii=False)[:8000])
        if r2.is_success and "rca_markdown" in body:
            print("\n(rca_markdown ilk 500 karakter)\n")
            print((body.get("rca_markdown") or "")[:500])

        # REST: govde script icinde sabit (MCP ciktisi ile ayni mock metin olabilir).
        print("\n--- POST /analyze/text (MCP ciktisina benzer govde) ---")
        payload = {
            "text": "Database connection timeout from payment service",
            "title": "DB timeout",
            "priority": "P1",
        }
        rt = client.post(f"{base}/analyze/text", json=payload)
        print("status:", rt.status_code)
        print(json.dumps(rt.json(), indent=2, ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()

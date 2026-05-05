"""Ollama erişilemediğinde hataları ayırt etmek için yardımcılar."""

from __future__ import annotations

import httpx

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


def ollama_unreachable(exc: BaseException) -> bool:
    """Bağlantı reddi / Ollama kapalı gibi durumlar."""
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)):
        return True
    if requests is not None and isinstance(exc, requests.exceptions.ConnectionError):
        return True
    msg = str(exc).lower()
    if "actively refused" in msg or "connection refused" in msg:
        return True
    if "failed to establish a new connection" in msg:
        return True
    if isinstance(exc, ValueError) and "inference endpoint" in str(exc):
        return True
    return False


OLLAMA_HINT_TR = (
    "Docker Compose: önce `docker compose up` ile `ollama` servisinin healthy olduğundan emin olun; "
    "modeller yoksa: `docker compose exec ollama ollama pull llama3` ve "
    "`docker compose exec ollama ollama pull nomic-embed-text`. "
    "Yerel Ollama kullanıyorsanız uygulamayı başlatın ve aynı pull komutlarını hostta çalıştırın."
)
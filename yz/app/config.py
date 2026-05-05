import os

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
KNOWLEDGE_DIR = os.environ.get("KNOWLEDGE_DIR", "knowledge")
CHROMA_DIR = os.environ.get("CHROMA_DIR", "data/chroma")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "4"))

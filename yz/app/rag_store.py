"""Chroma + Ollama embedding ile RAG indeksi."""

import shutil
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHROMA_DIR, KNOWLEDGE_DIR, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL

_vectorstore: Chroma | None = None
_COLLECTION = "itsm_kb"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_documents() -> list[Document]:
    root = _project_root()
    kdir = root / KNOWLEDGE_DIR
    docs: list[Document] = []
    if not kdir.is_dir():
        return docs
    for path in sorted(kdir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": path.name}))
    for path in sorted(kdir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": path.name}))
    return docs


def _build_from_docs(embeddings: Embeddings, persist: str) -> Chroma:
    root = _project_root()
    raw_docs = _load_documents()
    if not raw_docs:
        raise RuntimeError(f"No documents in {root / KNOWLEDGE_DIR}. Add .md or .txt files.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    splits = splitter.split_documents(raw_docs)
    Path(persist).mkdir(parents=True, exist_ok=True)
    return Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=persist,
        collection_name=_COLLECTION,
    )


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    embeddings = OllamaEmbeddings(
        model=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    root = _project_root()
    persist = str(root / CHROMA_DIR)
    Path(persist).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=persist)
    names = {c.name for c in client.list_collections()}
    if _COLLECTION in names:
        _vectorstore = Chroma(
            persist_directory=persist,
            embedding_function=embeddings,
            collection_name=_COLLECTION,
        )
    else:
        _vectorstore = _build_from_docs(embeddings, persist)
    return _vectorstore


def refresh_vectorstore() -> Chroma:
    """Bilgi tabanı veya embedding modeli değişince indeksi sıfırdan kur."""
    global _vectorstore
    _vectorstore = None
    root = _project_root()
    persist = root / CHROMA_DIR
    if persist.exists():
        shutil.rmtree(persist)
    return get_vectorstore()

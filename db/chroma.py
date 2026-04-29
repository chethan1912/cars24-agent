import chromadb
from chromadb.config import Settings
from core.config import settings

_client = None


def get_chroma_client() -> chromadb.Client:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_PATH
        )
    return _client

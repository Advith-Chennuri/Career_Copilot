import os
import chromadb

# Set database persistence path to backend/chroma_db
CHROMA_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
)

_chroma_client = None

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Initializes and returns a globally cached persistent ChromaDB client.
    """
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _chroma_client

def get_kb_collection() -> chromadb.Collection:
    """
    Retrieves or creates the primary RAG collection 'knowledge_base'
    representing the student's study resources.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(name="knowledge_base")

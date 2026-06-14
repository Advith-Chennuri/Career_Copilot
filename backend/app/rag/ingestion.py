import logging
from typing import List
from app.rag.chroma_client import get_kb_collection
from app.rag.embeddings import get_embeddings_batch

logger = logging.getLogger(__name__)

def split_text(text: str, chunk_size: int = 600, chunk_overlap: int = 100) -> List[str]:
    """
    Splits text into chunks using a character-based sliding window with overlap.
    """
    if not text.strip():
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_length:
            break
        # Shift start back by overlap
        start = end - chunk_overlap
        
    return chunks

def ingest_document(filename: str, text: str, chunk_size: int = 600, chunk_overlap: int = 100) -> int:
    """
    Splits text into chunks, generates vector embeddings, and saves them
    into the ChromaDB knowledge base collection.
    
    Returns:
        int: The number of ingested document chunks.
    """
    chunks = split_text(text, chunk_size, chunk_overlap)
    if not chunks:
        logger.warning(f"No chunks extracted from file: {filename}")
        return 0
        
    logger.info(f"Splitting document '{filename}' into {len(chunks)} chunks.")
    
    try:
        # Generate batch embeddings for all chunks in a single request
        embeddings = get_embeddings_batch(chunks)
        
        # Prepare metadata and IDs
        ids = [f"{filename}_chunk_{idx}" for idx in range(len(chunks))]
        metadatas = [{"source": filename, "chunk_index": idx} for idx in range(len(chunks))]
        
        collection = get_kb_collection()
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunks
        )
        logger.info(f"Ingested {len(chunks)} chunks for '{filename}' into ChromaDB.")
        return len(chunks)
    except Exception as e:
        logger.exception(f"Error during ingestion of '{filename}' into ChromaDB")
        raise e

import pytest
from unittest.mock import patch, MagicMock
from app.rag.ingestion import split_text, ingest_document
from app.rag.retrieval import retrieve_context

def test_split_text_sliding_window():
    """
    Test character-based text splitting yields correct chunk sizes and overlaps.
    """
    text = "a" * 1000
    # Split size 400, overlap 100
    # Chunk 1: 0 - 400
    # Chunk 2: 300 - 700
    # Chunk 3: 600 - 1000
    chunks = split_text(text, chunk_size=400, chunk_overlap=100)
    assert len(chunks) == 3
    assert all(len(c) == 400 for c in chunks)
    # Validate content overlap boundary
    assert chunks[1] == "a" * 400

def test_split_text_empty():
    assert split_text("") == []
    assert split_text("   ") == []

@patch("app.rag.ingestion.get_kb_collection")
@patch("app.rag.ingestion.get_embeddings_batch")
def test_ingest_document_success(mock_embeddings, mock_collection_getter):
    """
    Test successful document ingestion processes text, generates embeddings,
    and calls ChromaDB collection upsert method.
    """
    mock_collection = MagicMock()
    mock_collection_getter.return_value = mock_collection
    
    # Mock return embeddings for 2 chunks
    mock_embeddings.return_value = [[0.05] * 768, [0.09] * 768]
    
    text = "This is segment one of notes." * 30  # ~900 characters -> 2 chunks
    chunks_count = ingest_document("aws_notes.pdf", text, chunk_size=600, chunk_overlap=100)
    
    assert chunks_count == 2
    assert mock_collection.add.called
    # Get parameters passed to add()
    called_args, called_kwargs = mock_collection.add.call_args
    assert "ids" in called_kwargs
    assert len(called_kwargs["ids"]) == 2
    assert called_kwargs["ids"][0] == "aws_notes.pdf_chunk_0"

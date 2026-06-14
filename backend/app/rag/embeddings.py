import logging
import random
from typing import List
from app.utils.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

def get_mock_embedding(text: str, dimension: int = 768) -> List[float]:
    """
    Generates a deterministic float list embedding based on text hash
    to support offline validation without remote API calls.
    """
    random.seed(hash(text))
    return [random.uniform(-0.1, 0.1) for _ in range(dimension)]

def get_embedding(text: str) -> List[float]:
    """
    Converts a single string of text into a high-dimensional vector embedding.
    """
    try:
        client = get_gemini_client()
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.warning(f"Falling back to mock embedding due to connection/key issue: {e}")
        return get_mock_embedding(text)

def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Converts a batch of texts into embeddings in a single request.
    """
    if not texts:
        return []
    try:
        client = get_gemini_client()
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=texts
        )
        return [emb.values for emb in response.embeddings]
    except Exception as e:
        logger.warning(f"Falling back to mock batch embeddings due to connection/key issue: {e}")
        return [get_mock_embedding(t) for t in texts]

"""
Embedding service using sentence-transformers.

Why sentence-transformers with local model instead of OpenAI embeddings?
1. No API costs - embeddings are cheap but add up at scale
2. No network latency for each embedding call
3. Privacy - resume data never leaves the machine
4. MiniLM-L6-v2 is ~80MB RAM, works fine on laptops

Model is loaded ONCE at startup (via FastAPI lifespan) because:
- Model loading takes 2-5 seconds
- Loading per-request would destroy response times
- Memory is allocated once, not leaked on each request
"""

from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from src.core.config import get_settings
from src.core.exceptions import EmbeddingError
from src.core.logging import logger


# Global model reference - initialized once via lifespan event
_embedding_model: SentenceTransformer | None = None


def initialize_embedding_model() -> None:
    """
    Load embedding model into memory.
    
    Call this ONCE at application startup, not per-request.
    Uses global state intentionally - model is heavyweight and stateless.
    """
    global _embedding_model
    
    if _embedding_model is not None:
        logger.warning("Embedding model already initialized, skipping reload")
        return
    
    settings = get_settings()
    model_name = settings.embedding_model
    
    logger.info(f"Loading embedding model: {model_name}")
    
    try:
        # device='cpu' because MiniLM is fast enough on CPU
        # and avoids CUDA memory issues on small GPUs
        _embedding_model = SentenceTransformer(model_name, device="cpu")
        
        # Warmup call - first encoding is slower due to JIT
        _ = _embedding_model.encode("warmup", convert_to_numpy=True)
        
        logger.info(f"Embedding model loaded successfully (dim={_embedding_model.get_sentence_embedding_dimension()})")
        
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise EmbeddingError(
            f"Could not load embedding model: {model_name}",
            details={"error": str(e)}
        )


def get_embedding_model() -> SentenceTransformer:
    """Get the loaded embedding model."""
    if _embedding_model is None:
        raise EmbeddingError(
            "Embedding model not initialized. Call initialize_embedding_model() first."
        )
    return _embedding_model


def generate_embedding(text: str) -> np.ndarray:
    """
    Generate embedding vector for text.
    
    Args:
        text: Text to encode (resume content or job description)
        
    Returns:
        NumPy array of floats (shape: [embedding_dim])
        
    Raises:
        EmbeddingError: If embedding generation fails
    """
    if not text or not text.strip():
        raise EmbeddingError("Cannot generate embedding for empty text")
    
    model = get_embedding_model()
    
    try:
        # Truncate very long text - model has token limit
        # MiniLM handles ~256 tokens well, ~512 max
        truncated = text[:4000]  # Rough char limit
        
        embedding = model.encode(
            truncated,
            convert_to_numpy=True,
            normalize_embeddings=True,  # Unit vectors for cosine similarity
        )
        
        return embedding
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise EmbeddingError(
            f"Failed to generate embedding: {str(e)}",
            details={"text_length": len(text)}
        )


def compute_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings.
    
    Note: If embeddings are normalized (which ours are), cosine similarity
    is just the dot product. But we compute it properly anyway for clarity.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Similarity score in range [-1, 1], where 1 is identical
    """
    # Ensure 1D arrays
    e1 = embedding1.flatten()
    e2 = embedding2.flatten()
    
    # Cosine similarity formula
    dot_product = np.dot(e1, e2)
    norm1 = np.linalg.norm(e1)
    norm2 = np.linalg.norm(e2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    
    # Clamp to valid range (floating point errors can push slightly outside)
    return float(np.clip(similarity, -1.0, 1.0))

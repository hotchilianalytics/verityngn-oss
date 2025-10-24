import logging
from typing import List

import numpy as np

from verityngn.config.settings import SEMANTIC_FILTER_ENABLED, SEMANTIC_FILTER_THRESHOLD

logger = logging.getLogger(__name__)

_EMBEDDER = None

def _load_embedder():
    global _EMBEDDER
    if _EMBEDDER is not None:
        return _EMBEDDER
    try:
        # Optional heavy dependency: only attempt if enabled
        if SEMANTIC_FILTER_ENABLED:
            from sentence_transformers import SentenceTransformer
            _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("[SEMANTIC] Loaded SentenceTransformer all-MiniLM-L6-v2")
        else:
            _EMBEDDER = None
    except Exception as e:
        logger.warning(f"[SEMANTIC] Failed to load MiniLM embedder (optional, disabled to reduce image size): {e}")
        _EMBEDDER = None
    return _EMBEDDER

def embed_texts(texts: List[str]) -> np.ndarray:
    model = _load_embedder()
    if model is None:
        # Fallback: return zero vectors to keep pipeline running
        return np.zeros((len(texts), 384), dtype=float)
    return np.array(model.encode(texts, normalize_embeddings=True))

def compute_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.ndim == 1:
        a = a.reshape(1, -1)
    if b.ndim == 1:
        b = b.reshape(1, -1)
    # cosine similarity of first vectors
    av = a[0]
    bv = b[0]
    denom = (np.linalg.norm(av) * np.linalg.norm(bv)) or 1.0
    return float(np.dot(av, bv) / denom)

def is_on_topic(main_context: str, candidate_title: str, candidate_desc: str, threshold: float = None) -> bool:
    if not SEMANTIC_FILTER_ENABLED:
        return True
    threshold = threshold if threshold is not None else SEMANTIC_FILTER_THRESHOLD
    try:
        ctx = main_context.strip()
        cand = f"{candidate_title} {candidate_desc}".strip()
        if not ctx or not cand:
            return True
        embs = embed_texts([ctx, cand])
        sim = compute_similarity(embs[0], embs[1])
        logger.info(f"[SEMANTIC] similarity={sim:.3f} threshold={threshold}")
        return sim >= threshold
    except Exception as e:
        logger.warning(f"[SEMANTIC] Fallback to heuristic due to error: {e}")
        return True


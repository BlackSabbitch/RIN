"""Vectorized cosine similarity — shared by memory/retrieval.py and
embryonic/numberbatch.py. Lives in memory/, not embryonic/, so that
memory/ (the generic Tier-1 substrate) never has to depend on
embryonic/ (Tier-2 content sourcing); embryonic/numberbatch.py imports
from here instead of the other way around.
"""

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two single vectors — the scalar case of
    cosine_similarities, for call sites comparing one pair at a time
    (e.g. memory/diffuse.py's per-node relevance gate) rather than one
    query against a whole candidate matrix.
    """
    return float(cosine_similarities(a, b.reshape(1, -1))[0])


def cosine_similarities(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity of `query` against every row of `matrix`, as
    one vectorized result — comparing one vector to many in a single
    matrix-vector product instead of a per-row Python loop. This was a
    measured bottleneck (ATOMIC linking over ~24k events taking several
    minutes) before being batched.

    Args:
        query: 1D vector, shape (dim,).
        matrix: 2D array of candidate rows, shape (n, dim).

    Returns:
        1D array of similarities, shape (n,). 0.0 for any row (or the
        query) with zero norm, instead of dividing by zero.
    """
    query_norm = np.linalg.norm(query)
    row_norms = np.linalg.norm(matrix, axis=1)
    denom = row_norms * query_norm
    return np.divide(matrix @ query, denom, out=np.zeros_like(denom), where=denom > 0)

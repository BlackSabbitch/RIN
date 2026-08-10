"""Retrieval Step 1 (anchoring): find nodes whose node.embedding is
close to a query vector. definitions.tex, "Retrieval": "RW для поиска
входа не годится (медленен, диффузен)" — this is deliberately not a
walk, just a vector comparison, same as any nearest-neighbor search.

Kept independent of embryonic/ (Numberbatch, ConceptNet): this module
only ever touches node.embedding — plain vectors already cached on the
graph — so it works regardless of which encoder produced them. Turning
a raw query string into vectors is a separate, encoder-specific concern;
see embryonic/linking.py for the Numberbatch version.
"""

import numpy as np

from memory.graph import MemoryGraph
from memory.similarity import cosine_similarities


def nearest_nodes_by_embedding(
    G: MemoryGraph,
    query_vector: np.ndarray,
    top_k: int = 3,
    min_similarity: float = 0.3,
) -> list[int]:
    """The `top_k` node ids whose node.embedding is closest to
    `query_vector` by cosine similarity, among nodes that have one.

    Stacks every embedded node's vector into one matrix and scores them
    as a single matrix-vector product (memory.similarity.cosine_similarities)
    rather than looping node by node — cheap at Tier-2 scale (hundreds to
    low thousands of nodes); a real ANN index (HNSW, per runtime.tex's
    cost table) only starts to matter around 10^6 nodes.

    Args:
        G: Graph to search. Nodes with embedding=None are skipped.
        query_vector: Vector in the same embedding space as node.embedding
            (same encoder — see module docstring).
        top_k: Max number of node ids to return.
        min_similarity: Nodes below this cosine similarity are dropped
            rather than returned, same reasoning as
            embryonic.numberbatch.Numberbatch.nearest_among's floor: an
            empty/irrelevant match set should come back empty, not force
            "closest of a bad set" as if it were a real hit.

    Returns:
        Up to `top_k` node ids at or above `min_similarity`, nearest
        first. Empty if nothing clears the floor.
    """
    embedded = [node for node in G.nodes.values() if node.embedding is not None]
    if not embedded:
        return []
    matrix = np.asarray([node.embedding for node in embedded], dtype=np.float32)
    query = np.asarray(query_vector, dtype=np.float32)
    similarities = cosine_similarities(query, matrix)
    order = np.argsort(-similarities)
    results = []
    for i in order:
        if similarities[i] < min_similarity:
            break
        results.append(embedded[i].id)
        if len(results) >= top_k:
            break
    return results

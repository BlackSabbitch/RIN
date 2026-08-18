"""Reusable graph priors for retrieval on top of MemoryGraph.

This module keeps global structural priors out of experiment notebooks,
so the same weighted PageRank / strength-based signals can later be
reused by retrieval code proper rather than copied cell-by-cell.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from memory.graph import MemoryGraph


def weighted_out_strengths(G: MemoryGraph) -> dict[int, float]:
    """Sum of outgoing edge weights for every node in ``G``."""
    strengths: dict[int, float] = {}
    for node_id in G.node_ids():
        strengths[node_id] = float(sum(edge.weight for edge in G.out_edges(node_id)))
    return strengths


def weighted_in_strengths(G: MemoryGraph) -> dict[int, float]:
    """Sum of incoming edge weights for every node in ``G``."""
    strengths: dict[int, float] = {node_id: 0.0 for node_id in G.node_ids()}
    for node_id in G.node_ids():
        for edge in G.out_edges(node_id):
            strengths[edge.dst] = strengths.get(edge.dst, 0.0) + float(edge.weight)
    return strengths


def normalize_positive_prior(
    values: dict[int, float], floor: float = 1e-12
) -> dict[int, float]:
    """Normalize arbitrary non-negative node scores into a prior.

    The returned prior always sums to 1 and is strictly positive after
    flooring, so downstream code can safely divide by ``prior[node_id]``
    without special-casing zero-strength nodes.
    """
    if not values:
        return {}
    clamped = {node_id: max(float(value), floor) for node_id, value in values.items()}
    total = sum(clamped.values())
    if total <= 0:
        uniform = 1.0 / len(clamped)
        return {node_id: uniform for node_id in clamped}
    return {node_id: value / total for node_id, value in clamped.items()}


def in_strength_prior(G: MemoryGraph, floor: float = 1e-12) -> dict[int, float]:
    """Normalized strictly-positive weighted in-strength prior."""
    return normalize_positive_prior(weighted_in_strengths(G), floor=floor)


def out_strength_prior(G: MemoryGraph, floor: float = 1e-12) -> dict[int, float]:
    """Normalized strictly-positive weighted out-strength prior."""
    return normalize_positive_prior(weighted_out_strengths(G), floor=floor)


def weighted_pagerank(
    G: MemoryGraph,
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-9,
) -> dict[int, float]:
    """Weighted PageRank over ``MemoryGraph`` via power iteration.

    Edge weights define the per-source transition split. Sink nodes
    redistribute their mass uniformly, matching the standard PageRank
    treatment that keeps the stationary distribution well-defined.
    """
    node_ids = list(G.node_ids())
    n_nodes = len(node_ids)
    if n_nodes == 0:
        return {}
    if not 0.0 <= damping < 1.0:
        raise ValueError("damping must be in [0.0, 1.0)")
    if max_iter <= 0:
        raise ValueError("max_iter must be positive")
    if tol < 0:
        raise ValueError("tol must be non-negative")

    index_of = {node_id: i for i, node_id in enumerate(node_ids)}
    outgoing: dict[int, list[tuple[int, float]]] = defaultdict(list)
    totals: dict[int, float] = {}
    for node_id in node_ids:
        edges = G.out_edges(node_id)
        total_weight = float(sum(edge.weight for edge in edges))
        totals[node_id] = total_weight
        if total_weight > 0:
            outgoing[node_id] = [
                (index_of[edge.dst], float(edge.weight)) for edge in edges
            ]

    scores = np.full(n_nodes, 1.0 / n_nodes, dtype=np.float64)
    teleport = (1.0 - damping) / n_nodes
    uniform_share = 1.0 / n_nodes

    for _ in range(max_iter):
        next_scores = np.full(n_nodes, teleport, dtype=np.float64)
        sink_mass = 0.0
        for node_id in node_ids:
            src_index = index_of[node_id]
            src_score = scores[src_index]
            total_weight = totals[node_id]
            if total_weight <= 0:
                sink_mass += src_score
                continue
            for dst_index, weight in outgoing[node_id]:
                next_scores[dst_index] += damping * src_score * (weight / total_weight)
        if sink_mass > 0:
            next_scores += damping * sink_mass * uniform_share
        if np.abs(next_scores - scores).sum() <= tol:
            scores = next_scores
            break
        scores = next_scores

    return {node_id: float(scores[index_of[node_id]]) for node_id in node_ids}

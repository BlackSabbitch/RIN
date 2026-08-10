"""Retrieval Step 2 (spreading): deterministic activation diffusion from
anchor nodes, per definitions.tex's activation equation:

    a(t+1) = lambda * P~^T * a(t) + s(t)

Not a random walker (see memory/walk.py for that — a different operator,
built for a different purpose, Tier-1's stationary-distribution
estimation). Here charge moves through *all* outgoing edges of an active
node simultaneously, split proportionally by edge weight (and, if
`query_vectors` is given, by query relevance — see `diffuse`'s
docstring), decayed by `decay` each step — order-free, deterministic,
and cheap (no simulated agents, just local sparse propagation bounded by
min_propagate_fraction).

restart=0.0 (the default) matches 04_walker.tex's policy table exactly:
retrieval's teleport probability alpha=0 — s(t) is only active at t=0,
a one-shot pulse that spreads and fades, not an ongoing restart. The
manual reserves restart/teleport (its eq:ppr, a(t)=(1-alpha)P^T a(t) +
alpha*r) explicitly for the *sleep* policy (large alpha), not retrieval
— so restart is exposed as an opt-in parameter for whenever a sleep-mode
diffusion is built, not turned on here by default.
"""

from collections import defaultdict

import numpy as np

from memory.graph import MemoryGraph
from memory.similarity import cosine_similarity


def diffuse(
    G: MemoryGraph,
    source_amplitudes: dict[int, float],
    decay: float = 0.8,
    min_propagate_fraction: float = 0.01,
    max_steps: int = 20,
    restart: float = 0.0,
    query_vectors: list[np.ndarray] | None = None,
) -> dict[int, float]:
    """Spread charge from `source_amplitudes` outward through G.

    Each step, every node whose *current* amplitude is still at or above
    the propagation floor (see min_propagate_fraction) sends its entire
    current amplitude to its out-neighbors, split proportional to edge
    weight — and, if `query_vectors` is given, also proportional to each
    neighbor's relevance to the query (04_walker.tex's `rel(B|q)` factor
    in `P(A->B) propto w_AB * rel(B|q) * mc(B|mood) * unc(B)^beta`; this
    implements only the `rel(B|q)` term, the others are mood/curiosity
    concerns not built yet) — scaled by `decay` (this is P~^T a(t),
    computed locally per active node rather than as a dense matrix
    multiply — cheap as long as the active frontier stays small, which
    decay + the floor guarantee). A node below the floor still keeps
    whatever amplitude it received (see Returns) but does not push it
    further — this is the "front boundary" naturally falling out of the
    same formula, not a separate mechanism.

    Without the gate (`query_vectors=None`, the default — unchanged
    behavior from before this parameter existed), diffusion ranks purely
    by topology: a node reachable from several directions accumulates
    amplitude regardless of whether it has anything to do with the
    query. Confirmed as a real defect on a hand-authored graph with a
    known correct answer (experiment 3): querying "why coffee gives
    energy" without the gate ranked the generic, well-connected
    "beverage" (146.67, fed from three directions) over the actually
    correct "caffeine" (26.67) by 5.5x. See experiment 4 for the same
    scenario re-run with the gate.

    This is a "hot potato" diffusion, matching a(t+1) = lambda*P~^T*a(t) +
    s(t) literally: with restart=0 (the default — see module docstring
    for why), a node's amplitude at step t+1 comes only from what flowed
    in that step, not from stacking on top of its own previous value —
    so amplitude rises when charge arrives and fades once it has moved
    on, unless neighbors keep refeeding it. Order doesn't matter: this
    is a deterministic recurrence over the whole active set per step,
    not a sequence of individual visits.

    Args:
        G: Graph to diffuse over; read-only (does not mutate G — unlike
            walk(), which writes to node.activation, diffuse() returns
            its own field so a caller can run several queries against
            the same G without them clobbering each other).
        source_amplitudes: node id -> injected amplitude, i.e. a(0)
            — typically the output of an anchoring step (e.g.
            memory/retrieval.py's nearest_nodes_by_embedding), given some
            starting charge per anchor (a flat 100 for every anchor is a
            reasonable default to start with).
        decay: lambda in the equation above, in (0, 1]. Fraction of an
            active node's amplitude that reaches its neighbors per step
            (before the edge-weighted split).
        min_propagate_fraction: The "front boundary" rule, expressed as
            a fraction of the largest injected amplitude rather than an
            absolute number — a node stops propagating once its current
            amplitude falls below `min_propagate_fraction *
            max(source_amplitudes.values())`. An absolute floor is
            scale-dependent (a floor of 1.0 only makes sense if you
            happen to inject around 100; inject 1.0 per anchor and
            nothing would propagate at all) — this is purely a
            computational cutoff either way (real diffusion has no
            floor); without it the frontier keeps expanding forever at
            vanishing amplitude.
        max_steps: Hard cap on steps, independent of amplitude — a safety
            valve against a decay/floor/restart combination that never
            quite dies out on a large or cyclic graph.
        restart: Fraction of the *original* source_amplitudes re-injected
            at every step (s(t) = restart * source_amplitudes for t > 0),
            on top of whatever flowed in from neighbors. 0.0 (default)
            means a one-shot pulse — matches retrieval's alpha=0 in
            04_walker.tex. A nonzero value turns this into a
            personalized-PageRank-style recurrence that keeps re-
            anchoring to the sources — appropriate for a sleep-style
            policy (04_walker.tex's alpha="большой"), not for retrieval:
            without decay eventually cutting it off, sustained restart
            drives the field toward the graph's dominant eigenvector,
            i.e. hub-dominated (the same pull battery test #1 measured),
            which is the opposite of what a query-local retrieval wants.
        query_vectors: Vectors in the same embedding space as
            node.embedding — typically embryonic.query.query_vectors's
            output, one per query content word/term, not mean-pooled
            (same multi-seed reasoning as anchoring itself: averaging
            "coffee" and "north dakota" would blur two unrelated topics
            into a meaningless point). None (default) disables the gate
            entirely, i.e. rel(B|q)=1 for every node — the original,
            topology-only behavior. When given, a node's relevance is
            the *maximum* cosine similarity across all query vectors
            (relevant to *any* query topic, not penalized for being
            irrelevant to the others), clipped to [0, 1] (a node
            opposed to the query attenuates propagation toward it, never
            amplifies it — cosine similarity is signed, but a "negative
            relevance" multiplying charge would flip its sign, which
            has no physical meaning here). A node with no embedding
            (e.g. an ATOMIC episode node — see
            embryonic.numberbatch.attach_embeddings) gets relevance 1.0:
            no basis to judge it, so it isn't penalized for lacking one.

    Returns:
        node id -> peak amplitude that node reached at any step
        (including the initial injection). This is what "collect the
        content of lit-up nodes" reads: a node that briefly lit up and
        then faded is still reported at its peak, not its (possibly
        near-zero) final value — a snapshot at any single step would
        depend on catching the right moment, which retrieval has no
        reason to know in advance.
    """
    relevance_cache: dict[int, float] = {}

    def relevance(node_id: int) -> float:
        if query_vectors is None:
            return 1.0
        if node_id not in relevance_cache:
            node = G.nodes[node_id]
            if node.embedding is None:
                relevance_cache[node_id] = 1.0
            else:
                best = max(cosine_similarity(node.embedding, qv) for qv in query_vectors)
                relevance_cache[node_id] = max(0.0, best)
        return relevance_cache[node_id]

    floor = min_propagate_fraction * max(source_amplitudes.values(), default=0.0)
    current: dict[int, float] = dict(source_amplitudes)
    peak: dict[int, float] = dict(current)
    for _step in range(max_steps):
        active = {node_id: amount for node_id, amount in current.items() if amount >= floor}
        if not active:
            break
        next_current: dict[int, float] = defaultdict(float)
        for node_id, amount in active.items():
            out_edges = G.out_edges(node_id)
            gated_weights = [edge.weight * relevance(edge.dst) for edge in out_edges]
            total_weight = sum(gated_weights)
            if total_weight <= 0:
                continue
            for edge, gated_weight in zip(out_edges, gated_weights):
                next_current[edge.dst] += decay * amount * (gated_weight / total_weight)
        if restart > 0:
            for node_id, amount in source_amplitudes.items():
                next_current[node_id] += restart * amount
        current = dict(next_current)
        for node_id, amount in current.items():
            if amount > peak.get(node_id, 0.0):
                peak[node_id] = amount
    return peak

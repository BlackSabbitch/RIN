"""Node confidence: source_trust(source) x kind_baseline(node_kind), not a
flat constant.

Two orthogonal factors, per node.py's own docstring ("node_kind ...
determines what confidence means", 01_substrate.tex "Виды узлов"):

- `node_kind` sets what confidence MEANS. A "concept" node (ConceptNet:
  "a mug is a container") is a truth-apt claim — confidence is belief in
  its truth. An "episode" node built from an ATOMIC social-causal
  dimension (xReact/xWant/...) is not truth-apt the same way — it's a
  crowd's soft estimate of how someone reacts, so its ceiling is lower
  even before considering where it came from.
- `source` sets a trust multiplier for *where the content came from*,
  independent of what kind of claim it is.

Multiplying the two keeps them separable instead of collapsing both into
one flat placeholder (the old DEFAULT_NODE_CONFIDENCE=0.7 duplicated
across conceptnet_source.py/atomic_source.py, and write_path.py's own
flat DEFAULT_SOURCE_TRUST=0.9) that couldn't distinguish a ConceptNet
fact from an ATOMIC reaction-guess, or a direct user statement from
either.

Both tables below are hand-set priors, not calibrated against anything —
there is no observation stream yet to confirm or contradict a prior
against (write-path exists now, but nothing consumes its commits to
check them against reality yet). They exist so different kinds/sources
start out honestly different from each other, not to pretend a precision
that isn't there. `source_trust` is deliberately kept as its own
function, not inlined, because it's the exact hook a future *learned*
version (adjusted from confirmed/contradicted write-path commits, per
01_substrate.tex's epistemic layer) replaces in place — callers don't
change, only the lookup's implementation does.
"""

# Per-origin trust, ordered by how directly the content reflects what it
# claims: a first-person statement from the user is closest to ground
# truth; ConceptNet's crowd-corroborated factual assertions next;
# ATOMIC's crowd-annotated *social* judgments last (a crowd's read on how
# PersonX reacts is intrinsically softer than "a mug is a container").
SOURCE_TRUST = {
    "user": 0.9,
    "conceptnet": 0.7,
    "atomic": 0.5,
}
DEFAULT_SOURCE_TRUST = 0.6  # unrecognized source: below any calibrated one, above zero


def source_trust(source: str) -> float:
    """Per-origin trust multiplier.

    `source` may be a plain key ("conceptnet", "atomic") or a
    "kind:detail" compound (write_path.Event.source, e.g.
    "user:yaroslav") — only the part before the first ":" is looked up,
    so which specific user/device asserted something doesn't change the
    trust tier, without needing a separate per-source-instance table.
    """
    key = source.split(":", 1)[0]
    return SOURCE_TRUST.get(key, DEFAULT_SOURCE_TRUST)


# What confidence MEANS differs by node_kind (see module docstring).
# Only "episode" is capped below full source trust right now; every
# other kind in 01_substrate.tex's taxonomy (claim, observation,
# relationship_state, ...) is truth-apt in the same sense "concept" is,
# so DEFAULT_KIND_BASELINE covers them without needing an entry each.
KIND_BASELINE = {
    "concept": 1.0,
    "episode": 0.7,
}
DEFAULT_KIND_BASELINE = 1.0


def baseline_confidence(source: str, node_kind: str) -> float:
    """confidence(node) = source_trust(source) x kind_baseline(node_kind).

    Structural, not calibrated: different (source, node_kind) pairs
    start out honestly different. Not derived from edge weight —
    ConceptNet's edge weight is corroboration of a *relation* (see
    conceptnet_source.py), a separate channel from how much to trust
    the *node's* content.
    """
    return source_trust(source) * KIND_BASELINE.get(node_kind, DEFAULT_KIND_BASELINE)

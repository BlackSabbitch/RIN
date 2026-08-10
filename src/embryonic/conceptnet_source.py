"""ConceptNet as a content source for the embryonic graph
(docs/graph_memory_manual/chapters/embryonic.tex).

Three loading strategies behind one shape (fetch edges for a term -> add
to a MemoryGraph):

- `seeded_subgraph`: live queries against the public ConceptNet API,
  breadth-first from a small seed list out to a bounded hop radius.
  Nothing is downloaded; this is the "засеянный подграф" method the
  manual recommends (embryonic.tex, "Как строить эмбрион").
- `seeded_subgraph_from_dump`: the same bounded BFS, but sourced from a
  local assertions dump instead of the live API — added because
  api.conceptnet.io has been returning 502 for over a day (see network
  note below) and a local dump was already on hand. Same output shape as
  `seeded_subgraph`; use whichever is available/preferred.
- `full_dump`: streams a local copy of the full assertions CSV with no
  seed/radius bound. This is the "слепой импорт" the manual explicitly
  warns against for actual memory content, kept here only because it was
  asked for explicitly. See the warning on `full_dump` before using it.

Network note: as of writing, https://api.conceptnet.io is returning 502
from its own nginx (the root domain conceptnet.io answers fine, so this
looks like an outage on their end, not a local network issue), which is
why `seeded_subgraph_from_dump` exists. This module's API-based
functions are implemented against the documented contract
(https://github.com/commonsense/conceptnet5/wiki/API) but have not been
exercised against a live successful response.
"""

import gzip
import json
import time
import urllib.parse
import urllib.request
from collections import defaultdict

from memory.edge import Edge
from memory.graph import MemoryGraph
from memory.node import Node

API_ROOT = "https://api.conceptnet.io"

# See seeded_subgraph_from_dump's "weight filter" note: RelatedTo is
# ConceptNet's catch-all, least-specific relation type, and empirically
# the dominant relation on hub/generic-word nodes ("place", "company")
# that pull unrelated content into a seeded subgraph — e.g. a weight-1.0
# "company RelatedTo purpose" edge, weight-1.0 being unremarkable (the
# single most common weight in the dump), so a blanket weight floor
# doesn't touch it, but a RelatedTo-specific floor does. Typed relations
# (IsA/AtLocation/UsedFor/...) don't show this pattern and keep the
# general, low floor.
DEFAULT_MIN_EDGE_WEIGHT = 0.0
DEFAULT_MIN_RELATED_TO_WEIGHT = 2.0


def _passes_weight_filter(
    rel_type: str, weight: float, min_edge_weight: float, min_related_to_weight: float
) -> bool:
    if rel_type == "RelatedTo":
        return weight >= min_related_to_weight
    return weight >= min_edge_weight

# ConceptNet's own edge weight reads as an out-of-the-box soft confidence
# (definitions.tex, "Провенанс"), but that is a statement about *edges*.
# For the *node* itself we still need a confidence value and don't have
# a principled source_trust() (01_substrate.tex's commit()) yet, so this
# is a placeholder "commonsense-source" baseline, not a calibrated value.
DEFAULT_NODE_CONFIDENCE = 0.7


def _normalize_term(term: str) -> str:
    """"Andrew Ng" -> "andrew_ng", ConceptNet's multi-word convention."""
    return term.strip().lower().replace(" ", "_")


def _concept_uri(term: str, language: str) -> str:
    return f"/c/{language}/{_normalize_term(term)}"


def _label_from_uri(uri: str) -> str:
    """"/c/en/andrew_ng" -> "andrew ng", for Node.content.

    ConceptNet URIs often carry extra segments after the term itself —
    a part-of-speech tag (/c/en/place/n) and sometimes a WordNet sense
    (/c/en/lead/n/wn/artifact). The term is always the segment right
    after the language code (uri.split("/") == ["", "c", lang, term,
    ...]); rsplit("/", 1)[-1] instead grabs the *last* segment, which for
    a POS/sense-tagged URI is "n"/"v"/"a"/"r" or a sense id, not the
    word — this used to silently mislabel a large fraction of nodes as
    a single letter.

    The POS tag, when present, is kept and appended as "term (pos)":
    ConceptNet routinely has both a bare /c/en/term node and a separate
    /c/en/term/n (or /a, /v, /r) node for the same word — genuinely
    different nodes with their own edges, not duplicates — and without
    some visible marker they render identically and read as duplicated
    edges. Deeper sense segments (the /wn/artifact part) are dropped;
    the full URI is always available via Node.provenance.
    """
    parts = uri.split("/")
    term = parts[3] if len(parts) > 3 else parts[-1]
    label = term.replace("_", " ")
    if len(parts) > 4 and parts[4]:
        label = f"{label} ({parts[4]})"
    return label


def fetch_concept_edges(
    term: str, language: str = "en", limit: int = 50, timeout: float = 10.0
) -> list[dict]:
    """Fetch one page of ConceptNet edges touching `term`.

    Single page only (no `view.nextPage` pagination) — a deliberate
    simplification; seeded_subgraph's limit_per_node keeps individual
    fetches small enough that this rarely matters for a Tier-1 seed set.

    Args:
        term: Concept term, e.g. "mug" or "Andrew Ng" (normalized
            internally; see _normalize_term).
        language: ConceptNet language code.
        limit: Max edges to request in the single page.
        timeout: HTTP timeout in seconds.

    Returns:
        The response's "edges" list (see API docs for the per-edge
        shape: start/end/rel/weight/surfaceText/@id), or [] on any
        request failure (network error, non-200, malformed JSON) —
        callers treat a term with no reachable data the same as a term
        with no edges, rather than crashing a whole BFS over one bad hop.
    """
    uri = _concept_uri(term, language)
    url = f"{API_ROOT}{uri}?limit={limit}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("edges", [])


def _same_language(endpoint: dict, language: str) -> bool:
    return endpoint.get("@id", "").startswith(f"/c/{language}/")


def _get_or_create_node(
    G: MemoryGraph, concept_to_id: dict[str, int], uri: str
) -> int:
    if uri in concept_to_id:
        return concept_to_id[uri]
    node_id = len(concept_to_id)
    concept_to_id[uri] = node_id
    G.add_node(
        Node(
            id=node_id,
            content=_label_from_uri(uri),
            node_kind="concept",
            confidence=DEFAULT_NODE_CONFIDENCE,
            provenance=[uri],
        )
    )
    return node_id


def seeded_subgraph(
    entries: list[str],
    radius: int,
    language: str = "en",
    limit_per_node: int = 50,
    max_nodes: int = 2000,
    request_delay: float = 0.5,
    min_edge_weight: float = DEFAULT_MIN_EDGE_WEIGHT,
    min_related_to_weight: float = DEFAULT_MIN_RELATED_TO_WEIGHT,
) -> MemoryGraph:
    """Breadth-first ConceptNet subgraph from `entries`, out to `radius` hops.

    This is the "seed -> k-hop expansion" half of embryonic.tex's build
    recipe; min_edge_weight/min_related_to_weight are the automatable
    part of its "weight filter" step (manual cleaning is still on you —
    see seeded_subgraph_from_dump's matching parameters for why RelatedTo
    gets its own, stricter floor).

    Args:
        entries: Seed concept terms, e.g. ["AI", "Andrew Ng", "Lisbon"].
        radius: Max hop distance from any seed to include. 0 means "only
            the seeds themselves, no expansion".
        language: ConceptNet language code; edges touching a different
            language are skipped rather than followed, to keep the
            subgraph monolingual.
        limit_per_node: Max edges fetched per concept (caps fan-out at
            hub concepts, e.g. very general terms, from exploding the
            subgraph).
        max_nodes: Hard cap on total concepts fetched, independent of
            radius — a safety valve against radius set too high on a
            hub-adjacent seed.
        request_delay: Seconds to sleep between API requests; the public
            API has no documented rate limit, this is just politeness.

    Returns:
        A MemoryGraph with one node per concept reached and one directed
        edge per ConceptNet assertion between two same-language concepts
        within the graph. Edge.type is the ConceptNet relation label
        (IsA, UsedFor, ...); Edge.weight is ConceptNet's own edge weight.
    """
    G = MemoryGraph()
    concept_to_id: dict[str, int] = {}
    visited: set[str] = set()
    frontier = [_concept_uri(term, language) for term in entries]
    hop = 0
    while frontier and hop <= radius and len(concept_to_id) < max_nodes:
        next_frontier: list[str] = []
        for uri in frontier:
            if uri in visited or len(concept_to_id) >= max_nodes:
                continue
            visited.add(uri)
            src_id = _get_or_create_node(G, concept_to_id, uri)
            term = uri.rsplit("/", 1)[-1]
            edges = fetch_concept_edges(term, language=language, limit=limit_per_node)
            time.sleep(request_delay)
            for edge in edges:
                start, end = edge.get("start", {}), edge.get("end", {})
                if not (_same_language(start, language) and _same_language(end, language)):
                    continue
                start_uri, end_uri = start["@id"], end["@id"]
                other_uri = end_uri if start_uri == uri else start_uri
                if len(concept_to_id) >= max_nodes and other_uri not in concept_to_id:
                    continue
                rel_type = edge.get("rel", {}).get("label", "RelatedTo")
                weight = float(edge.get("weight", 1.0))
                if not _passes_weight_filter(rel_type, weight, min_edge_weight, min_related_to_weight):
                    continue
                dst_id = _get_or_create_node(G, concept_to_id, other_uri)
                if start_uri == uri:
                    G.add_edge(Edge(src=src_id, dst=dst_id, type=rel_type, weight=weight))
                else:
                    G.add_edge(Edge(src=dst_id, dst=src_id, type=rel_type, weight=weight))
                if hop < radius and other_uri not in visited:
                    next_frontier.append(other_uri)
        frontier = next_frontier
        hop += 1
    return G


def build_language_adjacency(
    path: str, language: str = "en"
) -> dict[str, list[tuple[str, str, float, bool, str]]]:
    """One streaming pass over a local dump, building an in-memory
    adjacency index restricted to `language`-`language` assertions.

    This is the expensive step of seeded_subgraph_from_dump (a few
    minutes and a few hundred MB to low GB of RAM, depending on how much
    of the 34M-edge dump is in `language`) — exposed as its own function
    so a caller running many BFS queries (e.g. an interactive notebook)
    can build it once and pass it to seeded_subgraph_from_dump's
    `adjacency` argument repeatedly, instead of rebuilding it per call.

    Each qualifying edge (start -> end) is indexed under *both* endpoints
    so seeded_subgraph_from_dump can expand a node regardless of whether
    it was that edge's start or end — same behavior as seeded_subgraph
    querying the API, which returns edges touching a term either way.
    This means that whenever BFS ends up visiting *both* endpoints of an
    edge (routine for any concept near a seed), it will encounter that
    same edge twice, once from each side; seeded_subgraph_from_dump
    dedupes using this tuple's `edge_uri`, so it is included here even
    though nothing in this function itself needs it.

    Args:
        path: Local path to a ConceptNet assertions CSV/CSV.GZ.
        language: ConceptNet language code; only start-end pairs both in
            this language are kept.

    Returns:
        uri -> list of (other_uri, relation_type, weight, is_start,
        edge_uri), where is_start is True if `uri` was the edge's start
        (so the eventual MemoryGraph edge should point uri -> other_uri)
        and False if `uri` was the end (other_uri -> uri). edge_uri is
        the dump's own assertion id (the CSV's first column), stable and
        identical for both of an edge's two adjacency entries.
    """
    adjacency: dict[str, list[tuple[str, str, float, bool, str]]] = defaultdict(list)
    opener = gzip.open if path.endswith(".gz") else open
    prefix = f"/c/{language}/"
    with opener(path, "rt", encoding="utf-8") as dump_file:
        for line in dump_file:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 5:
                continue
            edge_uri, relation, start, end, metadata_json = fields[:5]
            if not (start.startswith(prefix) and end.startswith(prefix)):
                continue
            try:
                metadata = json.loads(metadata_json)
            except json.JSONDecodeError:
                metadata = {}
            weight = float(metadata.get("weight", 1.0))
            rel_type = relation.rsplit("/", 1)[-1]
            adjacency[start].append((end, rel_type, weight, True, edge_uri))
            adjacency[end].append((start, rel_type, weight, False, edge_uri))
    return adjacency


def seeded_subgraph_from_dump(
    entries: list[str],
    radius: int,
    path: str | None = None,
    adjacency: dict[str, list[tuple[str, str, float, bool]]] | None = None,
    language: str = "en",
    limit_per_node: int | None = 50,
    max_nodes: int = 2000,
    min_edge_weight: float = DEFAULT_MIN_EDGE_WEIGHT,
    min_related_to_weight: float = DEFAULT_MIN_RELATED_TO_WEIGHT,
) -> MemoryGraph:
    """seeded_subgraph's bounded BFS, sourced from a local dump instead
    of the live API — see module docstring for when to use which.

    Either `path` or a pre-built `adjacency` (from build_language_adjacency)
    must be given. Pass `path` for a one-off query; build the adjacency
    index once yourself and pass it via `adjacency` when running many
    queries against the same dump (e.g. from a notebook), to skip
    re-streaming the whole file every time. No network calls either way,
    no `request_delay` needed.

    Args:
        entries: Seed concept terms, e.g. ["AI", "Andrew Ng", "Lisbon"].
        radius: Max hop distance from any seed. 0 means seeds only.
        path: Local path to a ConceptNet assertions CSV/CSV.GZ. Ignored
            if `adjacency` is given.
        adjacency: A pre-built index from build_language_adjacency, for
            the "build once, query many times" case. If None, built from
            `path` for this call only.
        language: ConceptNet language code for both the index (if built
            here) and the seed terms.
        limit_per_node: Max neighbors followed per concept, highest
            ConceptNet weight first. None follows all of them — a hub
            concept's full local dump neighbor list can be large, unlike
            the API path where the server-side page size already caps it.
        max_nodes: Hard cap on total concepts fetched.
        min_edge_weight: Minimum ConceptNet weight for any edge to be
            followed/kept, except RelatedTo (see min_related_to_weight).
            The default (0.0) keeps everything; typed relations rarely
            need a floor here since their weight-1.0 default isn't the
            noise source RelatedTo is.
        min_related_to_weight: Minimum weight specifically for RelatedTo
            edges — ConceptNet's least-specific relation, and empirically
            the one that pulls generic hub concepts (and, through them,
            unrelated content) into a seeded subgraph. See module-level
            DEFAULT_MIN_RELATED_TO_WEIGHT for the reasoning behind 2.0.

    Returns:
        A MemoryGraph in the same shape as seeded_subgraph's.

    Raises:
        ValueError: neither path nor adjacency was given.
    """
    if adjacency is None:
        if path is None:
            raise ValueError("seeded_subgraph_from_dump needs path or adjacency")
        adjacency = build_language_adjacency(path, language)
    G = MemoryGraph()
    concept_to_id: dict[str, int] = {}
    visited: set[str] = set()
    # Every edge is indexed under both endpoints (see
    # build_language_adjacency), so BFS meets it twice — once from each
    # side — whenever both endpoints get visited. seen_edges, keyed by
    # the dump's own assertion id, makes sure each underlying assertion
    # still becomes exactly one Edge in G.
    seen_edges: set[str] = set()
    frontier = [_concept_uri(term, language) for term in entries]
    hop = 0
    while frontier and hop <= radius and len(concept_to_id) < max_nodes:
        next_frontier: list[str] = []
        for uri in frontier:
            if uri in visited or len(concept_to_id) >= max_nodes:
                continue
            visited.add(uri)
            src_id = _get_or_create_node(G, concept_to_id, uri)
            neighbors = [
                entry
                for entry in adjacency.get(uri, [])
                if _passes_weight_filter(entry[1], entry[2], min_edge_weight, min_related_to_weight)
            ]
            if limit_per_node is not None and len(neighbors) > limit_per_node:
                neighbors = sorted(neighbors, key=lambda item: item[2], reverse=True)
                neighbors = neighbors[:limit_per_node]
            for other_uri, rel_type, weight, is_start, edge_uri in neighbors:
                if len(concept_to_id) >= max_nodes and other_uri not in concept_to_id:
                    continue
                other_id = _get_or_create_node(G, concept_to_id, other_uri)
                if edge_uri not in seen_edges:
                    seen_edges.add(edge_uri)
                    if is_start:
                        G.add_edge(Edge(src=src_id, dst=other_id, type=rel_type, weight=weight))
                    else:
                        G.add_edge(Edge(src=other_id, dst=src_id, type=rel_type, weight=weight))
                if hop < radius and other_uri not in visited:
                    next_frontier.append(other_uri)
        frontier = next_frontier
        hop += 1
    return G


def full_dump(
    path: str, language: str | None = "en", limit: int | None = None
) -> MemoryGraph:
    """Stream-parse a local ConceptNet assertions CSV into a MemoryGraph.

    This is the "слепой импорт" embryonic.tex argues against for real
    memory content (noise, staleness, weak relevance to any one persona)
    — kept here as an explicit, opt-in capability, not the default path.
    It also does not scale the way seeded_subgraph does: the full dump
    is ~34M edges. Loading that many Node/Edge dataclass instances into
    process memory is a multi-tens-of-GB operation on most machines, not
    a "just try it" thing — always pass `limit` unless you specifically
    need the whole graph and know your machine can hold it.

    Does not download anything: `path` must already point at a local
    `conceptnet-assertions-*.csv.gz` (or decompressed `.csv`), e.g. from
    https://github.com/commonsense/conceptnet5/wiki/Downloads.

    Args:
        path: Local path to the assertions file, gzip or plain text.
        language: If set, only assertions where both endpoints are in
            this ConceptNet language are kept; multilingual bridging
            edges and other languages are skipped. None keeps everything.
        limit: Max number of assertion rows to read before stopping.
            None reads the entire file — see the memory warning above.

    Returns:
        A MemoryGraph built the same way as seeded_subgraph's (concept
        nodes, typed/weighted directed edges), just from the bulk file
        instead of the API.
    """
    G = MemoryGraph()
    concept_to_id: dict[str, int] = {}
    opener = gzip.open if path.endswith(".gz") else open
    count = 0
    with opener(path, "rt", encoding="utf-8") as dump_file:
        for line in dump_file:
            if limit is not None and count >= limit:
                break
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 5:
                continue
            _uri, relation, start, end, metadata_json = fields[:5]
            if language is not None and not (
                start.startswith(f"/c/{language}/") and end.startswith(f"/c/{language}/")
            ):
                continue
            try:
                metadata = json.loads(metadata_json)
            except json.JSONDecodeError:
                metadata = {}
            weight = float(metadata.get("weight", 1.0))
            rel_type = relation.rsplit("/", 1)[-1]
            src_id = _get_or_create_node(G, concept_to_id, start)
            dst_id = _get_or_create_node(G, concept_to_id, end)
            G.add_edge(Edge(src=src_id, dst=dst_id, type=rel_type, weight=weight))
            count += 1
    return G

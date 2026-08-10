"""Unified embryonic-graph loading interface (embryonic.tex).

One class, one (`entries`, `radius`) surface, three backends per source
underneath — see EmbryonicGraphLoader's docstring for why "full" and
"seeded" can't share an implementation even though they share an
interface, and why "seeded" itself has two interchangeable backends.
"""

from memory.graph import MemoryGraph

from embryonic import atomic_source, conceptnet_source
from embryonic.conceptnet_source import DEFAULT_MIN_EDGE_WEIGHT, DEFAULT_MIN_RELATED_TO_WEIGHT
from embryonic.numberbatch import DEFAULT_MIN_SIMILARITY, Numberbatch, attach_embeddings

FULL = "full"


class EmbryonicGraphLoader:
    """Build an embryonic MemoryGraph from ConceptNet (+ optionally ATOMIC).

    Two modes behind one interface:

    - Seeded: `entries=["AI", "Andrew Ng", "Lisbon"], radius=3` — a
      bounded k-hop subgraph from those terms. This is embryonic.tex's
      recommended "засеянный подграф" method and is the intended common
      case. Two interchangeable backends, chosen by `conceptnet_backend`:
      `"api"` (default) queries the live ConceptNet API and downloads
      nothing; `"local_dump"` runs the same bounded BFS over a local
      assertions dump instead (needs conceptnet_dump_path) — added
      because api.conceptnet.io has had an extended outage (502) and a
      local dump may already be on hand. Same output shape either way.
    - Full: `entries=["full"]` (radius is then ignored) — streams a
      local ConceptNet assertions dump with no seed/radius bound
      (conceptnet_source.full_dump). This is the "слепой импорт"
      embryonic.tex argues against for actual memory content; it exists
      here because it was asked for explicitly, not as a recommendation.
      Needs conceptnet_dump_path; never downloads anything itself, and
      can consume tens of GB of memory without conceptnet_full_limit —
      see conceptnet_source.full_dump's docstring before using it.

    ATOMIC (optional, any mode): set `include_atomic=True` with
    `atomic_path` and `numberbatch_path` pointing at already-downloaded
    local files — ATOMIC has no query API, so unlike ConceptNet it can't
    be fetched lazily; see atomic_source's module docstring for how
    "seeded" is approximated for it instead (filtering by ConceptNet-
    concept linkage rather than by hop distance).

    Embeddings: whenever a Numberbatch source is configured
    (`numberbatch_path` or `numberbatch`) — independent of
    `include_atomic` — `load()` also fills in `node.embedding` for
    ConceptNet concept nodes via `numberbatch.attach_embeddings`. This is
    the prerequisite for any retrieval operator that anchors via vector
    search (definitions.tex, "Retrieval", Step 1); without it every node
    in the graph has `embedding=None`.

    There is no default for `entries`: instantiating this class without
    deciding what you want raises, rather than silently defaulting to
    "full" and attempting a multi-GB load the first time someone forgets
    to pass an argument.
    """

    def __init__(
        self,
        entries: list[str] | None = None,
        radius: int = 2,
        language: str = "en",
        conceptnet_backend: str = "api",
        conceptnet_dump_path: str | None = None,
        conceptnet_adjacency: dict | None = None,
        conceptnet_full_limit: int | None = None,
        limit_per_node: int | None = 50,
        max_nodes: int = 2000,
        request_delay: float = 0.5,
        min_edge_weight: float = DEFAULT_MIN_EDGE_WEIGHT,
        min_related_to_weight: float = DEFAULT_MIN_RELATED_TO_WEIGHT,
        include_atomic: bool = False,
        atomic_path: str | None = None,
        numberbatch_path: str | None = None,
        numberbatch: Numberbatch | None = None,
        linking_min_similarity: float = DEFAULT_MIN_SIMILARITY,
        atomic_fuzzy_linking: bool = False,
    ) -> None:
        """
        Args:
            entries: Seed concept terms for seeded mode, or exactly
                ["full"] to opt into full-dump mode.
            radius: Max hop distance from any seed (seeded mode only;
                ignored in full mode). Must be a finite non-negative int.
            language: ConceptNet language code, used by all sources.
            conceptnet_backend: "api" (live, default) or "local_dump"
                (needs conceptnet_dump_path) — which ConceptNet source
                seeded mode uses. Ignored in full mode, which always
                reads conceptnet_dump_path.
            conceptnet_dump_path: Local path to a ConceptNet assertions
                CSV/CSV.GZ. Required for full mode, and for seeded mode
                with conceptnet_backend="local_dump" unless
                conceptnet_adjacency is given instead; unused otherwise.
            conceptnet_adjacency: A pre-built index from
                conceptnet_source.build_language_adjacency, for reusing
                one index across several loaders/queries instead of
                re-streaming conceptnet_dump_path each time (seeded mode,
                local_dump backend only). Takes precedence over
                conceptnet_dump_path when both are given.
            conceptnet_full_limit: Full mode only — max assertion rows to
                read. None reads the whole file — see the memory warning
                above.
            limit_per_node: Seeded mode only — max neighbors followed per
                concept (highest ConceptNet weight first for
                local_dump). None follows all of them.
            max_nodes: Seeded mode only — hard cap on concepts fetched.
            request_delay: Seeded mode, "api" backend only — seconds
                between API calls; unused for local_dump (no network).
            min_edge_weight: Seeded mode only — forwarded to
                conceptnet_source's seeded_subgraph(_from_dump); the
                automatable half of embryonic.tex's "weight filter" step.
            min_related_to_weight: Seeded mode only — stricter floor
                specifically for RelatedTo edges, ConceptNet's least-
                specific relation and empirically the one that pulls
                generic hub concepts (and through them, unrelated
                ATOMIC events) into a seeded subgraph; see
                conceptnet_source.DEFAULT_MIN_RELATED_TO_WEIGHT.
            include_atomic: Whether to also load ATOMIC events and link
                them to the ConceptNet concepts already loaded.
            atomic_path: Local path to an ATOMIC CSV (see
                atomic_source.load_atomic_csv for the expected schema —
                the aggregated one, e.g. v4_atomic_all_agg.csv, not the
                per-annotator raw one). Required if include_atomic.
            numberbatch_path: Local path to a Numberbatch embeddings
                file. Required for ATOMIC-to-ConceptNet linking if
                include_atomic is True, unless `numberbatch` is given
                instead; also used (with or without include_atomic) to
                attach embeddings to concept nodes — see the class
                docstring's "Embeddings" paragraph.
            numberbatch: A pre-loaded Numberbatch instance, for reusing
                one already-parsed embeddings file across several
                loaders instead of re-parsing numberbatch_path (a
                multi-GB file) on every .load() call. Takes precedence
                over numberbatch_path when both are given.
            linking_min_similarity: Forwarded to
                atomic_source.add_events_to_graph / Numberbatch.nearest_among
                — only used if atomic_fuzzy_linking=True (see below); an
                absolute cosine floor that turned out too permissive to
                be the default.
            atomic_fuzzy_linking: Forwarded to add_events_to_graph's
                fuzzy_fallback. Defaults to False — ATOMIC events link to
                ConceptNet concepts by exact lemma match only, no
                threshold needed. True re-enables the known-too-
                permissive embedding fallback; see
                embryonic/linking.py's link_event_to_concepts docstring
                for why this isn't the default (in short: an absolute
                cosine floor can't be calibrated without a downstream
                retrieval metric to check it against — deferred, not
                forgotten).

        Raises:
            ValueError: entries is None; include_atomic is True without
                (atomic_path and (numberbatch_path or numberbatch)); or
                conceptnet_backend is not "api" or "local_dump".
        """
        if entries is None:
            raise ValueError(
                "entries is required — pass a seed list (e.g. "
                '["AI", "Andrew Ng", "Lisbon"]) for a bounded subgraph, '
                'or entries=["full"] to explicitly opt into loading full '
                "local dumps (see conceptnet_source.full_dump's warning "
                "about memory use before doing that)."
            )
        if include_atomic and not (atomic_path and (numberbatch_path or numberbatch)):
            raise ValueError(
                "include_atomic=True requires atomic_path and either "
                "numberbatch_path or a pre-loaded numberbatch (ATOMIC has "
                "no query API and needs Numberbatch to link its events to "
                "ConceptNet concepts; see embryonic/linking.py)."
            )
        if conceptnet_backend not in ("api", "local_dump"):
            raise ValueError('conceptnet_backend must be "api" or "local_dump"')
        self.entries = list(entries)
        self.radius = radius
        self.language = language
        self.conceptnet_backend = conceptnet_backend
        self.conceptnet_dump_path = conceptnet_dump_path
        self.conceptnet_adjacency = conceptnet_adjacency
        self.conceptnet_full_limit = conceptnet_full_limit
        self.limit_per_node = limit_per_node
        self.max_nodes = max_nodes
        self.request_delay = request_delay
        self.min_edge_weight = min_edge_weight
        self.min_related_to_weight = min_related_to_weight
        self.include_atomic = include_atomic
        self.atomic_path = atomic_path
        self.numberbatch_path = numberbatch_path
        self.numberbatch = numberbatch
        self.linking_min_similarity = linking_min_similarity
        self.atomic_fuzzy_linking = atomic_fuzzy_linking

    @property
    def is_full(self) -> bool:
        """True iff entries is exactly the ["full"] sentinel."""
        return self.entries == [FULL]

    def load(self) -> MemoryGraph:
        """Build the embryonic MemoryGraph for this configuration.

        Returns:
            A MemoryGraph with node_kind="concept" nodes from ConceptNet
            (embedded, if a Numberbatch source is configured — see the
            class docstring's "Embeddings" paragraph) and, if
            include_atomic, node_kind="episode" nodes from ATOMIC,
            cross-linked via embryonic/linking.py.
        """
        G = self._load_full() if self.is_full else self._load_seeded()
        if self.numberbatch is not None or self.numberbatch_path is not None:
            attach_embeddings(G, self._ensure_numberbatch())
        return G

    def _concept_id_index(self, G: MemoryGraph) -> dict[str, int]:
        # Depends on conceptnet_source always storing the concept URI as
        # provenance[0] on "concept" nodes — an internal contract between
        # this module and conceptnet_source, not a general MemoryGraph
        # invariant.
        return {
            node.provenance[0]: node.id
            for node in G.nodes.values()
            if node.node_kind == "concept" and node.provenance
        }

    def _ensure_numberbatch(self) -> Numberbatch:
        # Lazily loads and caches on self, so a loader used for both
        # ATOMIC linking and embedding attachment (or multiple .load()
        # calls) only ever parses numberbatch_path once.
        if self.numberbatch is None:
            self.numberbatch = Numberbatch()
            self.numberbatch.load(self.numberbatch_path)
        return self.numberbatch

    def _add_atomic(self, G: MemoryGraph, *, require_concept_link: bool) -> None:
        numberbatch = self._ensure_numberbatch()
        events = atomic_source.load_atomic_csv(self.atomic_path)
        atomic_source.add_events_to_graph(
            G,
            events,
            concept_to_id=self._concept_id_index(G),
            numberbatch=numberbatch,
            language=self.language,
            require_concept_link=require_concept_link,
            min_similarity=self.linking_min_similarity,
            fuzzy_fallback=self.atomic_fuzzy_linking,
        )

    def _load_seeded(self) -> MemoryGraph:
        if self.conceptnet_backend == "local_dump":
            if not (self.conceptnet_dump_path or self.conceptnet_adjacency):
                raise ValueError(
                    'conceptnet_backend="local_dump" needs conceptnet_dump_path '
                    "or a pre-built conceptnet_adjacency"
                )
            G = conceptnet_source.seeded_subgraph_from_dump(
                entries=self.entries,
                radius=self.radius,
                path=self.conceptnet_dump_path,
                adjacency=self.conceptnet_adjacency,
                language=self.language,
                limit_per_node=self.limit_per_node,
                max_nodes=self.max_nodes,
                min_edge_weight=self.min_edge_weight,
                min_related_to_weight=self.min_related_to_weight,
            )
        else:
            G = conceptnet_source.seeded_subgraph(
                entries=self.entries,
                radius=self.radius,
                language=self.language,
                limit_per_node=self.limit_per_node or 50,
                max_nodes=self.max_nodes,
                request_delay=self.request_delay,
                min_edge_weight=self.min_edge_weight,
                min_related_to_weight=self.min_related_to_weight,
            )
        if self.include_atomic:
            # require_concept_link=True: this is what makes ATOMIC
            # "seeded" at all, since it has no hop-radius query of its
            # own (see atomic_source module docstring).
            self._add_atomic(G, require_concept_link=True)
        return G

    def _load_full(self) -> MemoryGraph:
        if not self.conceptnet_dump_path:
            raise ValueError(
                "entries=['full'] needs conceptnet_dump_path (a local "
                "conceptnet-assertions-*.csv.gz) — full mode never "
                "downloads anything itself."
            )
        G = conceptnet_source.full_dump(
            self.conceptnet_dump_path,
            language=self.language,
            limit=self.conceptnet_full_limit,
        )
        if self.include_atomic:
            self._add_atomic(G, require_concept_link=False)
        return G

"""ConceptNet Numberbatch embeddings: the entity/event-linking bridge
used by linking.py, per embryonic.tex ("Мост через контент-слова и
Numberbatch"). No live API exists for this — the embeddings file must
already be downloaded locally (see
https://github.com/commonsense/conceptnet-numberbatch), e.g.
numberbatch-19.08.txt.gz (multilingual, ~3.2GB) or the English-only
variant. This module does not download it.
"""

import gzip

import numpy as np

from memory.graph import MemoryGraph
from memory.similarity import cosine_similarities

# Below this cosine similarity, treat a word as having no ConceptNet
# match rather than force-linking it to whatever happens to be least
# dissimilar. Unrelated word pairs in Numberbatch typically sit near 0;
# genuinely related ones sit meaningfully higher. Tune empirically —
# this is a starting point, not a calibrated value.
DEFAULT_MIN_SIMILARITY = 0.3


class Numberbatch:
    """In-memory Numberbatch vocabulary + vectorized nearest neighbor.

    Vectors are stored as one (vocab_size, dim) float32 numpy matrix
    plus a term<->row index, not a dict of Python lists: comparing a
    query against N candidates one Python float-loop at a time (the
    original implementation) was the actual bottleneck behind ATOMIC
    linking taking several minutes over ~24k events — nearest_among now
    does the whole candidate set as one matrix-vector product instead of
    a per-candidate loop. numpy is already a transitive dependency
    (matplotlib/networkx), so this adds nothing new to install.

    Loading the full multilingual file (~9.2M terms) still means several
    GB resident (float32 halves the old float-list memory footprint, but
    it's still all in RAM — no on-disk/lazy index).
    """

    def __init__(self) -> None:
        self.matrix: np.ndarray = np.empty((0, 0), dtype=np.float32)
        self.terms: list[str] = []
        self.term_to_index: dict[str, int] = {}

    def load(self, path: str, language: str = "en") -> None:
        """Parse a Numberbatch word2vec-text file (gzip or plain) into
        self.matrix/self.terms/self.term_to_index, with terms normalized
        to full ConceptNet URIs (e.g. "/c/en/mug") regardless of which
        file variant this is.

        The multilingual file (numberbatch-19.08.txt.gz) stores full
        URIs already. The English-only file (numberbatch-en-19.08.txt.gz)
        stores bare terms ("mug", not "/c/en/mug") since there is no
        language to disambiguate — this was silently mismatching every
        lookup against ConceptNet URIs (which always carry the prefix)
        until this normalization was added. Detected per-line rather
        than from the filename, so both variants load into the same key
        format transparently.

        Args:
            path: Local path to a numberbatch-*.txt(.gz) file.
            language: ConceptNet language code to prefix bare terms with;
                only used if this file turns out to store bare terms.
                Irrelevant for the multilingual file, which already
                carries its own per-term language in the URI.
        """
        opener = gzip.open if path.endswith(".gz") else open
        prefix = f"/c/{language}/"
        with opener(path, "rt", encoding="utf-8") as embeddings_file:
            header = embeddings_file.readline()
            vocab_size, dim = (int(value) for value in header.split())
            matrix = np.empty((vocab_size, dim), dtype=np.float32)
            terms: list[str] = []
            for line in embeddings_file:
                term, rest = line.rstrip("\n").split(" ", 1)
                if not term.startswith("/c/"):
                    term = f"{prefix}{term}"
                # np.fromstring(sep=...) is the fast path for parsing a
                # whitespace-separated text row directly into a float
                # array — much cheaper than building a Python list of
                # floats first and converting.
                matrix[len(terms)] = np.fromstring(rest, dtype=np.float32, sep=" ")
                terms.append(term)
        self.matrix = matrix[: len(terms)]
        self.terms = terms
        self.term_to_index = {term: index for index, term in enumerate(terms)}

    def vector_for(self, term: str) -> np.ndarray | None:
        """The stored vector for `term` (e.g. "/c/en/mug"), or None.

        Returns a view into self.matrix, not a copy.
        """
        index = self.term_to_index.get(term)
        return None if index is None else self.matrix[index]

    def nearest_among(
        self,
        term: str,
        candidates: list[str],
        top_k: int = 1,
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
    ) -> list[str]:
        """The `top_k` of `candidates` closest to `term` by cosine similarity.

        Used by linking.py as the embedding fallback when a lemma match
        between an ATOMIC content word and a ConceptNet term fails
        (embryonic.tex's link_atomic_event_to_concepts pseudocode).

        Args:
            term: Query term; must be a key in self.term_to_index
                (typically a single content word, embedded the same way
                a concept is, since Numberbatch is a concept-level, not
                token-level, embedding).
            candidates: Terms to rank against `term` — pass a small,
                already-relevant set (e.g. the concepts already present
                in a seeded subgraph), not the whole vocabulary. Scored
                as one batched matrix operation, not a per-candidate
                loop, so this is cheap even for a few thousand candidates.
            top_k: How many nearest candidates to return.
            min_similarity: Candidates below this cosine similarity are
                dropped rather than returned. Without this floor, a
                completely unrelated candidate set still produces a
                "nearest" result — this used to make link_event_to_concepts
                force-link content words to whatever concept happened to
                be least dissimilar, however unrelated.

        Returns:
            Up to `top_k` candidate terms at or above `min_similarity`,
            nearest first. Empty if `term` has no stored vector, or none
            of `candidates` clears the floor.
        """
        query_index = self.term_to_index.get(term)
        if query_index is None:
            return []
        valid_candidates = [c for c in candidates if c in self.term_to_index]
        if not valid_candidates:
            return []
        candidate_rows = [self.term_to_index[c] for c in valid_candidates]
        query = self.matrix[query_index]
        candidate_matrix = self.matrix[candidate_rows]
        similarities = cosine_similarities(query, candidate_matrix)
        order = np.argsort(-similarities)
        results = []
        for i in order:
            if similarities[i] < min_similarity:
                break
            results.append(valid_candidates[i])
            if len(results) >= top_k:
                break
        return results


def attach_embeddings(G: MemoryGraph, numberbatch: Numberbatch) -> int:
    """Fill in node.embedding for every node whose provenance is a
    Numberbatch-lookupable term, from an already-loaded Numberbatch.

    A separate pass rather than something conceptnet_source/atomic_source
    do at node-creation time, so those modules don't need to take a
    Numberbatch dependency just to build a graph — call this afterward
    whenever embeddings are wanted (needed before any retrieval operator
    that anchors via vector search on node.embedding; see definitions.tex,
    "Retrieval", Step 1).

    In practice this only fills in ConceptNet "concept" nodes: their
    provenance[0] is the exact ConceptNet URI Numberbatch is keyed by.
    ATOMIC "episode" nodes' provenance is either "atomic" or a parent
    node id (int), neither of which is a Numberbatch key, and their
    content is a multi-word phrase anyway — Numberbatch is a per-term,
    not per-sentence, embedding, so those nodes are left as-is here.

    Args:
        G: Graph to update in place.
        numberbatch: Already-loaded Numberbatch instance.

    Returns:
        Number of nodes that got an embedding attached.
    """
    attached = 0
    for node in G.nodes.values():
        if node.embedding is not None or not node.provenance:
            continue
        source = node.provenance[0]
        if not isinstance(source, str):
            continue
        vector = numberbatch.vector_for(source)
        if vector is not None:
            node.embedding = vector
            attached += 1
    return attached

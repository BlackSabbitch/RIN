"""Entity/event linking: connect an ATOMIC event phrase to ConceptNet
concepts, per embryonic.tex ("Мост через контент-слова и Numberbatch").
Without this, ATOMIC's social-causal knowledge ("PersonX breaks a cup")
and ConceptNet's taxonomic knowledge ("a cup is crockery") stay two
disconnected graphs instead of one embryonic graph.
"""

from embryonic.numberbatch import DEFAULT_MIN_SIMILARITY, Numberbatch

STOPWORDS = {
    "personx", "persony", "a", "an", "the", "to", "of", "in", "on", "at",
    "for", "and", "or", "is", "was", "be", "been", "being", "s",
    # Added for query.py's use on natural-language queries (not just
    # ATOMIC's templated event phrases, which never had "what"/"i"/"me"
    # etc. to begin with) — without these, greedy longest-match happily
    # anchors on real-but-meaningless Numberbatch entries like
    # "/c/en/what_is" or "/c/en/to_the" (corpus bigram artifacts).
    "i", "me", "my", "you", "your", "we", "our", "they", "them", "it",
    "its", "this", "that", "these", "those", "what", "who", "where",
    "when", "why", "how", "which", "tell", "about", "with", "do", "does",
    "did", "can", "could", "would", "should", "will", "shall", "have",
    "has", "had", "are", "were",
}


def content_words(phrase: str) -> list[str]:
    """Lowercased, stopword- and placeholder-free tokens from an ATOMIC
    event phrase, e.g. "PersonX breaks a cup" -> ["breaks", "cup"].

    Deliberately simple (no lemmatization, no POS tagging): lemma_match
    in link_event_to_concepts already has an embedding fallback for
    exactly the cases this misses (e.g. "breaks" not matching a
    ConceptNet term for "break").
    """
    tokens = phrase.lower().replace("'", " ").split()
    return [
        token.strip(".,!?_")
        for token in tokens
        if token.strip(".,!?_") not in STOPWORDS and token.strip(".,!?_")
    ]


def link_event_to_concepts(
    event_phrase: str,
    conceptnet_terms: set[str],
    numberbatch: Numberbatch,
    language: str = "en",
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
    fuzzy_fallback: bool = False,
) -> list[str]:
    """Map an ATOMIC event phrase to ConceptNet concept URIs.

    embryonic.tex's full two-step match is exact lemma match against
    `conceptnet_terms` first, Numberbatch nearest-neighbor fallback
    second — but the fallback's absolute-cosine floor (min_similarity)
    turned out to be the wrong instrument: in a ~300-dim space, almost
    any word finds *something* above a fixed floor among a few hundred
    diverse candidates (this is what let ~450k spurious ATOMIC links
    through against a 400-concept pool). The right instrument is a
    relative test — Lowe's ratio test (accept top-1 only if it clearly
    beats top-2) — but its own margin/ratio parameter is exactly as
    uncalibratable *right now* as min_similarity was: there is no
    downstream signal yet (no retrieval/diffusion) to tell a good
    threshold from a bad one. So for now `fuzzy_fallback` defaults to
    False — exact lemma match only, which needs no threshold at all —
    and the ratio-test + lemmatization (so more words hit exact match
    and never need the fallback) are deferred until diffusion gives an
    actual metric to calibrate against.

    Args:
        event_phrase: Raw ATOMIC event text, e.g. "PersonX breaks a cup".
        conceptnet_terms: Concept URIs already present in the graph
            being built (e.g. MemoryGraph node provenance/content from a
            seeded ConceptNet subgraph) — the candidate pool to link
            into, not the whole of ConceptNet.
        numberbatch: Loaded Numberbatch instance for the embedding
            fallback (only used if fuzzy_fallback=True).
        language: ConceptNet language code, used to build the candidate
            URI for each content word before checking conceptnet_terms.
        min_similarity: Only used if fuzzy_fallback=True; forwarded to
            Numberbatch.nearest_among. See the TODO above — this floor
            is known to be too permissive, kept only for when
            fuzzy_fallback is explicitly opted into.
        fuzzy_fallback: If False (default), only exact lemma matches
            count — a content word with no exact match is simply left
            unlinked. If True, re-enables the embedding fallback with
            its known-too-permissive absolute floor; opt-in only.

    Returns:
        One concept URI per content word that could be linked; words
        that match neither are dropped rather than raising, since
        partial linking of an event is expected, not an error.
    """
    concepts: list[str] = []
    for word in content_words(event_phrase):
        candidate_uri = f"/c/{language}/{word}"
        if candidate_uri in conceptnet_terms:
            concepts.append(candidate_uri)
        elif fuzzy_fallback:
            nearest = numberbatch.nearest_among(
                candidate_uri, list(conceptnet_terms), top_k=1, min_similarity=min_similarity
            )
            if nearest:
                concepts.append(nearest[0])
    return concepts

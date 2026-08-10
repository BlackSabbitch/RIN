"""Query anchoring — Step 1 of retrieval (definitions.tex, "Retrieval"):
turn raw query text into a set of vectors to search node.embedding with
(memory/retrieval.py's nearest_nodes_by_embedding).

Uses greedy longest-match against Numberbatch's own vocabulary, not a
naive per-word split: ConceptNet has real multi-word concept nodes
(/c/en/quantum_mechanics, /c/en/north_dakota, /c/en/movie_theater — all
three confirmed present in the actual dump, not hypothetical), and
splitting a query into single words before lookup can never anchor on
one directly — "north dakota" would look up "north" and "dakota"
separately, each a different, more generic concept than the compound.
Still not the full extraction pipeline the "Точки входа" manual section
describes (NER, clause-level units, LLM escalation for messy queries) —
that stays open for later; this closes specifically the multi-word gap.
"""

import numpy as np

from embryonic.linking import STOPWORDS
from embryonic.numberbatch import Numberbatch

MAX_NGRAM = 4  # longest phrase considered; ConceptNet's own multi-word
# terms are essentially all <=4 tokens, and larger spans get expensive
# to try at every position for no real payoff.


def longest_match_terms(
    query_text: str, numberbatch: Numberbatch, language: str = "en", max_ngram: int = MAX_NGRAM
) -> list[str]:
    """Greedily match the longest possible word-span at each position
    against Numberbatch's vocabulary, so a multi-word concept is
    anchored as one unit instead of decomposing into its individual
    words.

    At each position, tries spans from `max_ngram` words down to 1,
    joins them with "_" (ConceptNet's own multi-word convention, e.g.
    "north_dakota"), and takes the first (i.e. longest) span whose
    "/c/{language}/..." URI has a Numberbatch vector. A lone single-word
    span is skipped (not counted as a match, position still advances)
    if that word is a stopword — multi-word spans are never filtered by
    the single-word stopword list, since a match like "quantum_mechanics"
    is unambiguous regardless of whether "quantum" or "mechanics" alone
    would be filtered.

    Args:
        query_text: Raw query, e.g. "what is quantum mechanics".
        numberbatch: Loaded Numberbatch instance.
        language: ConceptNet language code for building candidate URIs.
        max_ngram: Longest word-span to try before falling back to
            shorter ones.

    Returns:
        Matched concept URIs, in the order their spans occur in the
        query. A span with no match at any length (down to 1) is simply
        skipped, not an error — partial anchoring is expected.
    """
    tokens = [tok for tok in query_text.lower().replace("'", " ").split() if tok.strip(".,!?_")]
    tokens = [tok.strip(".,!?_") for tok in tokens]
    n_tokens = len(tokens)
    matched_uris: list[str] = []
    i = 0
    while i < n_tokens:
        matched = False
        for n in range(min(max_ngram, n_tokens - i), 0, -1):
            span = tokens[i : i + n]
            if all(tok in STOPWORDS for tok in span):
                i += n
                matched = True
                break
            uri = f"/c/{language}/{'_'.join(span)}"
            if uri in numberbatch.term_to_index:
                matched_uris.append(uri)
                i += n
                matched = True
                break
        if not matched:
            i += 1
    return matched_uris


def query_vectors(
    query_text: str, numberbatch: Numberbatch, language: str = "en", max_ngram: int = MAX_NGRAM
) -> list[np.ndarray]:
    """Match `query_text` against Numberbatch's vocabulary via
    longest_match_terms and look up each matched term's vector.

    One vector per matched term, not mean-pooled: per the multi-seed
    principle discussed for retrieval, averaging "lisbon" and "seattle"
    into one vector would blur two distinct entities into a meaningless
    middle point — each term anchors independently instead (see
    memory/retrieval.py's caller for how multiple anchors are used).

    Args:
        query_text: Raw query, e.g. "what is the difference between
            lisbon and seattle".
        numberbatch: Loaded Numberbatch instance.
        language: ConceptNet language code, forwarded to longest_match_terms.
        max_ngram: Forwarded to longest_match_terms.

    Returns:
        One vector per matched term (longest_match_terms already
        guarantees each has a Numberbatch entry).
    """
    return [
        numberbatch.vector_for(uri)
        for uri in longest_match_terms(query_text, numberbatch, language, max_ngram)
    ]

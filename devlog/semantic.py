"""TF-IDF semantic search for devlog entries using numpy cosine similarity."""
from __future__ import annotations
import math
import re
from collections import Counter

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())

def _build_idf(docs: list[list[str]]) -> dict[str, float]:
    n = len(docs)
    df: Counter = Counter()
    for tokens in docs:
        df.update(set(tokens))
    return {w: math.log((n + 1) / (df[w] + 1)) + 1.0 for w in df}

def _tfidf_vector(tokens: list[str], idf: dict[str, float], vocab: list[str]) -> list[float]:
    tf = Counter(tokens)
    total = len(tokens) or 1
    return [tf.get(w, 0) / total * idf.get(w, 0.0) for w in vocab]

def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0

def semantic_search(query: str, entries: list[dict], top_k: int = 10) -> list[tuple[dict, float]]:
    """Return up to top_k entries ranked by TF-IDF cosine similarity to query."""
    if not entries:
        return []
    docs = [_tokenize(e["text"]) for e in entries]
    query_tokens = _tokenize(query)
    idf = _build_idf(docs + [query_tokens])
    vocab = list(idf.keys())
    vecs = [_tfidf_vector(d, idf, vocab) for d in docs]
    q_vec = _tfidf_vector(query_tokens, idf, vocab)
    scored = [(entries[i], _cosine(q_vec, vecs[i])) for i in range(len(entries))]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [(e, s) for e, s in scored[:top_k] if s > 0.0]

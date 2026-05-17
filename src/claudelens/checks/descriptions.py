"""Detect skills whose descriptions are semantically too close."""
from __future__ import annotations

import math
import re
from collections import Counter
from itertools import combinations

from claudelens.checks.base import Finding, Severity
from claudelens.config import Config
from claudelens.skill import Skill

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]+")
_STOPWORDS = frozenset(
    {
        "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
        "is", "are", "be", "this", "that", "these", "those", "as", "by", "at",
        "from", "into", "use", "uses", "used", "using", "user", "users",
        "when", "where", "what", "which", "who", "how", "why", "you", "your",
        "it", "its", "if", "but", "not", "no", "yes", "do", "does", "did",
        "should", "must", "may", "can", "will", "would", "any", "all", "also",
        "skill", "skills", "claude", "code", "tool", "tools",
    }
)


def check_descriptions(skills: list[Skill], config: Config) -> list[Finding]:
    """Pairwise similarity over description text.

    Uses sentence-transformers if available (better quality); otherwise falls
    back to TF-IDF cosine over token bags.
    """
    if len(skills) < 2:
        return []

    threshold = config.thresholds.description_similarity
    sims = _similarity_matrix([s.description for s in skills])

    findings: list[Finding] = []
    for i, j in combinations(range(len(skills)), 2):
        a, b = skills[i], skills[j]
        if config.is_ignored(a.name, b.name):
            continue
        score = sims[i][j]
        if score >= threshold:
            severity = Severity.ERROR if score >= threshold + 0.08 else Severity.WARNING
            findings.append(
                Finding(
                    check="descriptions.overlap",
                    severity=severity,
                    skills=(a.name, b.name),
                    message=(
                        f"Descriptions of '{a.name}' and '{b.name}' overlap "
                        f"(similarity={score:.2f}); routing may be ambiguous"
                    ),
                    score=score,
                )
            )
    return findings


def _similarity_matrix(texts: list[str]) -> list[list[float]]:
    """Try semantic embeddings; fall back to TF-IDF cosine."""
    try:
        return _embedding_similarity(texts)
    except Exception:
        return _tfidf_similarity(texts)


def _embedding_similarity(texts: list[str]) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    n = len(texts)
    sims = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            sims[i][j] = float(sum(a * b for a, b in zip(embeddings[i], embeddings[j])))
    return sims


def _tfidf_similarity(texts: list[str]) -> list[list[float]]:
    docs = [_tokenize(t) for t in texts]
    df: Counter[str] = Counter()
    for d in docs:
        df.update(set(d))
    n_docs = len(docs)

    def vec(tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        return {
            term: (count / len(tokens)) * math.log((1 + n_docs) / (1 + df[term]) + 1)
            for term, count in tf.items()
        }

    vectors = [vec(d) for d in docs]

    def cos(a: dict[str, float], b: dict[str, float]) -> float:
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot = sum(a[t] * b[t] for t in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    n = len(texts)
    sims = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            sims[i][j] = cos(vectors[i], vectors[j])
    return sims


def _tokenize(text: str) -> list[str]:
    return [
        t.lower()
        for t in _TOKEN_RE.findall(text)
        if t.lower() not in _STOPWORDS and len(t) > 2
    ]

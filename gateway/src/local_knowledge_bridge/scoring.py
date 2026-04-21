from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .constants import DEFAULT_SCORING
from .normalize import normalize_whitespace

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]*|[\u4e00-\u9fff]+")

SYNONYM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"sentinel-2", "sentinel2", "s2", "msi"}),
    frozenset({"sentinel-1", "sentinel1", "s1", "sar"}),
    frozenset({"lake", "lakes", "alpine lake", "glacial lake", "pond", "ponds", "reservoir", "reservoirs"}),
    frozenset({"water", "waters", "water body", "water bodies", "surface water", "inland water"}),
    frozenset({"mapping", "map", "inventory", "inventories", "classification", "delineation", "extraction"}),
    frozenset({"flood", "flooding", "inundation"}),
    frozenset({"wetland", "wetlands", "vegetated water"}),
)


@dataclass(frozen=True)
class QueryContext:
    query: str
    base_tokens: list[str]
    expanded_tokens: list[str]
    query_ngrams: Counter[str]
    fts_query: str


def scoring_defaults() -> dict[str, float | int]:
    return dict(DEFAULT_SCORING)


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_RE.findall((text or "").lower()):
        token = match.strip()
        if not token:
            continue
        if len(token) == 1 and "\u4e00" <= token <= "\u9fff":
            continue
        tokens.append(token)
        if "\u4e00" <= token[0] <= "\u9fff" and len(token) > 2:
            tokens.extend(token[idx : idx + 2] for idx in range(len(token) - 1))
    return tokens


def char_ngrams(text: str, n: int = 3) -> Counter[str]:
    compact = re.sub(r"\s+", "", (text or "").lower())[:8000]
    if not compact:
        return Counter()
    if len(compact) < n:
        return Counter({compact: 1})
    return Counter(compact[idx : idx + n] for idx in range(len(compact) - n + 1))


def cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = set(left).intersection(right)
    numerator = sum(left[key] * right[key] for key in overlap)
    if numerator <= 0:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm <= 0 or right_norm <= 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def expand_query_tokens(query: str) -> tuple[list[str], list[str]]:
    base = tokenize(query)
    expanded = list(base)
    base_set = set(base)
    lowered = (query or "").lower()
    for group in SYNONYM_GROUPS:
        if base_set.intersection(group) or any(term in lowered for term in group):
            expanded.extend(group)
    return base, list(dict.fromkeys(expanded))


def build_fts_query(query: str, expanded_tokens: list[str]) -> str:
    normalized_query = normalize_whitespace(query or "")
    terms: list[str] = []
    if normalized_query:
        escaped_query = normalized_query.replace('"', '""')
        terms.append(f'"{escaped_query}"')
    for token in expanded_tokens:
        normalized_token = normalize_whitespace(token)
        if not normalized_token:
            continue
        escaped_token = normalized_token.replace('"', '""')
        terms.append(f'"{escaped_token}"')
    unique_terms = list(dict.fromkeys(terms))
    if not unique_terms:
        return '""'
    return " OR ".join(unique_terms)


def build_query_context(query: str, scoring: dict[str, float | int] | None = None) -> QueryContext:
    settings = scoring or DEFAULT_SCORING
    base_tokens, expanded_tokens = expand_query_tokens(query)
    n = max(1, int(settings.get("char_ngram_n", DEFAULT_SCORING["char_ngram_n"])))
    return QueryContext(
        query=query,
        base_tokens=base_tokens,
        expanded_tokens=expanded_tokens,
        query_ngrams=char_ngrams(query, n=n),
        fts_query=build_fts_query(query, expanded_tokens),
    )


def lexical_score(text: str, title: str, tokens: list[str], scoring: dict[str, float | int] | None = None) -> float:
    settings = scoring or DEFAULT_SCORING
    lowered_text = (text or "").lower()
    lowered_title = (title or "").lower()
    title_hit_cap = int(settings.get("title_hit_cap", DEFAULT_SCORING["title_hit_cap"]))
    text_hit_cap = int(settings.get("text_hit_cap", DEFAULT_SCORING["text_hit_cap"]))
    title_hit_weight = float(settings.get("title_hit_weight", DEFAULT_SCORING["title_hit_weight"]))
    text_hit_weight = float(settings.get("text_hit_weight", DEFAULT_SCORING["text_hit_weight"]))
    title_contains_bonus = float(settings.get("title_contains_bonus", DEFAULT_SCORING["title_contains_bonus"]))

    score = 0.0
    for token in tokens:
        title_hits = min(title_hit_cap, lowered_title.count(token))
        text_hits = min(text_hit_cap, lowered_text.count(token))
        score += (title_hits * title_hit_weight) + (text_hits * text_hit_weight)
        if token in lowered_title:
            score += title_contains_bonus
    return score


def hybrid_score(
    text: str,
    title: str,
    base_tokens: list[str],
    expanded_tokens: list[str],
    query_ngrams: Counter[str],
    scoring: dict[str, float | int] | None = None,
) -> float:
    settings = scoring or DEFAULT_SCORING
    lexical = lexical_score(text, title, base_tokens, settings)
    expanded_lexical = lexical_score(text, title, expanded_tokens, settings)
    expansion_bonus = max(0.0, expanded_lexical - lexical) * float(
        settings.get("expansion_bonus_weight", DEFAULT_SCORING["expansion_bonus_weight"])
    )
    semantic = cosine(char_ngrams(f"{title}\n{text}", n=int(settings.get("char_ngram_n", DEFAULT_SCORING["char_ngram_n"]))), query_ngrams)
    return lexical + expansion_bonus + (
        semantic * float(settings.get("char_ngram_weight", DEFAULT_SCORING["char_ngram_weight"]))
    )


def semantic_score(
    text: str,
    title: str,
    query_ngrams: Counter[str],
    scoring: dict[str, float | int] | None = None,
) -> float:
    settings = scoring or DEFAULT_SCORING
    n = int(settings.get("char_ngram_n", DEFAULT_SCORING["char_ngram_n"]))
    return cosine(char_ngrams(f"{title}\n{text}", n=n), query_ngrams) * float(
        settings.get("semantic_char_ngram_weight", DEFAULT_SCORING["semantic_char_ngram_weight"])
    )


def fts_bonus(bm25_score: float, scoring: dict[str, float | int] | None = None) -> float:
    settings = scoring or DEFAULT_SCORING
    return max(
        0.0,
        float(settings.get("fts_bonus_base", DEFAULT_SCORING["fts_bonus_base"]))
        - (float(bm25_score) * float(settings.get("fts_bonus_scale", DEFAULT_SCORING["fts_bonus_scale"]))),
    )


def score_document(
    *,
    mode: str,
    title: str,
    body: str,
    bm25_score: float,
    query_context: QueryContext,
    scoring: dict[str, float | int] | None = None,
) -> dict[str, float]:
    settings = scoring or DEFAULT_SCORING
    lexical = lexical_score(body, title, query_context.base_tokens, settings)
    lexical_total = lexical + fts_bonus(bm25_score, settings)
    hybrid_total = hybrid_score(
        body,
        title,
        query_context.base_tokens,
        query_context.expanded_tokens,
        query_context.query_ngrams,
        settings,
    ) + fts_bonus(bm25_score, settings)
    semantic_total = semantic_score(body, title, query_context.query_ngrams, settings) + fts_bonus(bm25_score, settings)

    if mode == "lexical":
        active = lexical_total
    elif mode == "semantic":
        active = semantic_total
    else:
        active = hybrid_total

    return {
        "active_score": active,
        "lexical_score": lexical_total,
        "hybrid_score": hybrid_total,
        "semantic_score": semantic_total,
    }

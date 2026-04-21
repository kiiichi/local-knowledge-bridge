from __future__ import annotations

import copy
import math

from .constants import RRF_K
from .deep_models import load_embedding_model, load_reranker_model
from .normalize import normalize_whitespace
from .service_models import SearchHit

SEMANTIC_SCORE_WEIGHT = 40.0
RERANK_SCORE_WEIGHT = 25.0


def model_text_for_hit(hit: SearchHit, limit: int) -> str:
    parts = [
        hit.title,
        normalize_whitespace(hit.locator),
        normalize_whitespace(hit.snippet),
        normalize_whitespace(hit.semantic_text)[:limit],
    ]
    return "\n".join(part for part in parts if part)


def _hit_key(hit: SearchHit) -> str:
    return hit.canonical_key or f"{hit.route}:{hit.path}:{hit.locator}"


def _copy_hit(hit: SearchHit) -> SearchHit:
    cloned = copy.deepcopy(hit)
    cloned.score = 0.0
    cloned.routes = list(hit.routes or ([hit.route] if hit.route else []))
    return cloned


def _fuse_rankings(rankings: dict[str, list[SearchHit]]) -> list[SearchHit]:
    merged: dict[str, SearchHit] = {}
    best_contribution: dict[str, float] = {}

    for hits in rankings.values():
        for rank, hit in enumerate(hits, start=1):
            contribution = 1.0 / (RRF_K + rank)
            key = _hit_key(hit)
            if key not in merged:
                merged[key] = _copy_hit(hit)
                best_contribution[key] = -1.0

            merged_hit = merged[key]
            merged_hit.score += contribution
            merged_hit.lexical_score = max(merged_hit.lexical_score, hit.lexical_score)
            merged_hit.hybrid_score = max(merged_hit.hybrid_score, hit.hybrid_score)
            merged_hit.semantic_score = max(merged_hit.semantic_score, hit.semantic_score)
            merged_hit.rerank_score = max(merged_hit.rerank_score, hit.rerank_score)
            for route in hit.routes or ([hit.route] if hit.route else []):
                if route and route not in merged_hit.routes:
                    merged_hit.routes.append(route)

            if contribution > best_contribution[key]:
                best_contribution[key] = contribution
                merged_hit.route = hit.route
                merged_hit.title = hit.title
                merged_hit.path = hit.path
                merged_hit.locator = hit.locator
                merged_hit.snippet = hit.snippet
                merged_hit.year = hit.year
                merged_hit.doi = hit.doi
                merged_hit.full_path = hit.full_path
                merged_hit.library_id = hit.library_id
                merged_hit.library_name = hit.library_name
                merged_hit.semantic_text = hit.semantic_text
                merged_hit.extra = dict(hit.extra)

    return sorted(
        merged.values(),
        key=lambda item: (item.score, item.semantic_score, item.hybrid_score, item.lexical_score, item.title.lower()),
        reverse=True,
    )


def _cosine_from_vectors(left: object, right: object) -> float:
    left_values = [float(value) for value in left]
    right_values = [float(value) for value in right]
    if len(left_values) != len(right_values):
        raise ValueError("Embedding vector length mismatch.")
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))
    if left_norm <= 0.0 or right_norm <= 0.0:
        return 0.0
    return sum(a * b for a, b in zip(left_values, right_values)) / (left_norm * right_norm)


def apply_semantic_fusion(query: str, hits: list[SearchHit], config: dict) -> list[SearchHit]:
    if not hits:
        return hits

    model = load_embedding_model(config)
    texts = [model_text_for_hit(hit, limit=500) for hit in hits]
    query_vector = model.encode([query], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)[0]
    doc_vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)

    semantic_ranked: list[tuple[float, SearchHit]] = []
    for hit, doc_vector in zip(hits, doc_vectors):
        semantic_score = _cosine_from_vectors(query_vector, doc_vector)
        hit.semantic_score = float(semantic_score)
        hit.score += max(0.0, float(semantic_score)) * SEMANTIC_SCORE_WEIGHT
        semantic_ranked.append((float(semantic_score), hit))

    semantic_ranked.sort(key=lambda pair: pair[0], reverse=True)
    return _fuse_rankings(
        {
            "semantic": [item[1] for item in semantic_ranked],
            "hybrid": hits,
        }
    )


def _sort_after_rerank(hit: SearchHit) -> tuple[float, str, int, str]:
    try:
        year_value = int(hit.year or "0")
    except ValueError:
        year_value = 0
    return (-hit.score, hit.source, -year_value, hit.title.lower())


def apply_reranker(query: str, hits: list[SearchHit], config: dict, top_k: int) -> list[SearchHit]:
    if top_k <= 0 or not hits:
        return hits

    reranker = load_reranker_model(config)
    target_hits = hits[:top_k]
    pairs = [(query, model_text_for_hit(hit, limit=700)) for hit in target_hits]
    scores = reranker.predict(pairs, show_progress_bar=False)

    for hit, score in zip(target_hits, scores):
        normalized = float(score)
        hit.rerank_score = normalized
        hit.score += normalized * RERANK_SCORE_WEIGHT

    hits.sort(key=_sort_after_rerank)
    return hits


def apply_deep_ranking(query: str, hits: list[SearchHit], config: dict, *, top_k_rerank: int) -> list[SearchHit]:
    ranked = apply_semantic_fusion(query, hits, config)
    return apply_reranker(query, ranked, config, top_k=top_k_rerank)

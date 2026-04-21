from __future__ import annotations

import copy

from .constants import DEFAULT_ROUTE_WEIGHTS, RRF_K
from .service_models import SearchHit


def fuse_hits(
    route_hits: dict[str, list[SearchHit]],
    *,
    route_weights: dict[str, float] | None = None,
    rrf_k: int = RRF_K,
) -> list[SearchHit]:
    merged: dict[str, SearchHit] = {}
    best_contribution: dict[str, float] = {}
    weights = route_weights or DEFAULT_ROUTE_WEIGHTS

    for route, hits in route_hits.items():
        weight = float(weights.get(route, 1.0))
        for rank, hit in enumerate(hits, start=1):
            contribution = weight / (rrf_k + rank)
            key = hit.canonical_key or f"{hit.route}:{hit.path}:{hit.locator}"
            if key not in merged:
                merged[key] = copy.deepcopy(hit)
                merged[key].score = 0.0
                merged[key].routes = []
                best_contribution[key] = -1.0

            merged_hit = merged[key]
            merged_hit.score += contribution
            merged_hit.lexical_score = max(merged_hit.lexical_score, hit.lexical_score)
            merged_hit.hybrid_score = max(merged_hit.hybrid_score, hit.hybrid_score)
            merged_hit.semantic_score = max(merged_hit.semantic_score, hit.semantic_score)
            merged_hit.rerank_score = max(merged_hit.rerank_score, hit.rerank_score)
            if route not in merged_hit.routes:
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
        key=lambda item: (
            item.score,
            item.rerank_score,
            item.semantic_score,
            item.hybrid_score,
            item.lexical_score,
            item.title.lower(),
        ),
        reverse=True,
    )

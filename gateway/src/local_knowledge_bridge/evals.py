from __future__ import annotations

import json
import math
import statistics
import time

from .config import load_config
from .paths import eval_cases_path
from .retrieval import search_local
from .service_models import SearchRequest


def evaluate_cases(config: dict | None = None, *, profile: str = "balanced", baseline: bool = False) -> dict:
    config = config or load_config()
    cases_path = eval_cases_path()
    if not cases_path.exists() or not cases_path.read_text(encoding="utf-8").strip():
        raise RuntimeError(f"Missing evaluation cases: {cases_path}")

    rows = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    recalls_5: list[float] = []
    recalls_10: list[float] = []
    mrr_10: list[float] = []
    ndcg_10: list[float] = []
    timings_ms: list[float] = []
    per_case: list[dict] = []

    active_profile = "fast" if baseline else profile
    active_mode = "lexical" if baseline else "hybrid"
    for case in rows:
        started = time.perf_counter()
        result = search_local(
            config,
            SearchRequest(
                query=case["query"],
                target=str(case.get("target", "both")),
                years=case.get("years"),
                folder=case.get("folder"),
                endnote_library=case.get("endnote_library"),
                profile=active_profile,
                mode=active_mode,
                limit=20,
                auto_refresh=False,
                refresh_now=False,
            ),
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        timings_ms.append(elapsed_ms)

        expected = list(case.get("must_have", []))
        ranked = [(hit.get("doi") or hit.get("title") or "") for hit in result["hits"][:10]]
        hit_positions = [ranked.index(value) + 1 for value in expected if value in ranked]

        recall5 = 1.0 if any(value in ranked[:5] for value in expected) else 0.0
        recall10 = 1.0 if any(value in ranked[:10] for value in expected) else 0.0
        mrr = 1.0 / min(hit_positions) if hit_positions else 0.0

        dcg = 0.0
        idcg = 0.0
        for idx, value in enumerate(ranked[:10], start=1):
            rel = 1.0 if value in expected else 0.0
            dcg += rel / math.log2(idx + 1)
        for idx in range(1, min(len(expected), 10) + 1):
            idcg += 1.0 / math.log2(idx + 1)
        ndcg = dcg / idcg if idcg else 0.0

        recalls_5.append(recall5)
        recalls_10.append(recall10)
        mrr_10.append(mrr)
        ndcg_10.append(ndcg)
        per_case.append(
            {
                "query": case["query"],
                "recall@5": recall5,
                "recall@10": recall10,
                "mrr@10": mrr,
                "ndcg@10": ndcg,
                "latency_ms": elapsed_ms,
                "top_hit": result["hits"][0]["title"] if result["hits"] else None,
            }
        )

    return {
        "profile": "baseline" if baseline else profile,
        "cases": len(rows),
        "metrics": {
            "Recall@5": statistics.fmean(recalls_5) if recalls_5 else 0.0,
            "Recall@10": statistics.fmean(recalls_10) if recalls_10 else 0.0,
            "MRR@10": statistics.fmean(mrr_10) if mrr_10 else 0.0,
            "nDCG@10": statistics.fmean(ndcg_10) if ndcg_10 else 0.0,
            "AvgLatencyMs": statistics.fmean(timings_ms) if timings_ms else 0.0,
        },
        "per_case": per_case,
    }


def render_eval(metrics: dict) -> str:
    lines = [
        f"PROFILE: {metrics['profile']}",
        f"CASES: {metrics['cases']}",
        "",
        "METRICS:",
    ]
    for key, value in metrics["metrics"].items():
        if isinstance(value, float):
            lines.append(f"- {key}: {value:.4f}")
        else:
            lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("CASES:")
    for case in metrics["per_case"]:
        lines.append(
            f"- {case['query']} | recall@5={case['recall@5']:.2f}"
            f" | mrr@10={case['mrr@10']:.2f}"
            f" | latency_ms={case['latency_ms']:.1f}"
            f" | top_hit={case['top_hit']}"
        )
    return "\n".join(lines)

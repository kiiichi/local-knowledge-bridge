from __future__ import annotations

from typing import Any


def format_hit_text(hit: dict[str, Any], index: int, explain: bool = False) -> str:
    lines = [
        f"[{index}] score={hit['score']:.6f} source={hit['source']} route={hit['route']} year={hit['year'] or '-'}",
        f"    title={hit['title'] or '-'}",
        f"    path={hit['path'] or '-'}",
    ]
    if hit.get("locator"):
        lines.append(f"    locator={hit['locator']}")
    if hit.get("doi"):
        lines.append(f"    doi={hit['doi']}")
    if hit.get("library_name"):
        lines.append(f"    library={hit['library_name']}")
    lines.append(f"    snippet={hit['snippet'] or '-'}")
    if explain:
        lines.append(f"    routes={', '.join(hit.get('routes') or []) or hit['route']}")
        lines.append(f"    lexical_score={hit['lexical_score']:.6f}")
        lines.append(f"    hybrid_score={hit['hybrid_score']:.6f}")
        lines.append(f"    canonical_key={hit['canonical_key']}")
    return "\n".join(lines)


def search_results_text(payload: dict[str, Any], explain: bool = False) -> str:
    if not payload.get("hits"):
        return f"No local results found for query: {payload.get('query', '')}"
    return "\n\n".join(
        format_hit_text(hit, index, explain=explain)
        for index, hit in enumerate(payload["hits"], start=1)
    )


def build_answer_payload(question: str, payload: dict[str, Any]) -> dict[str, Any]:
    hits = payload.get("hits", [])
    if not hits:
        answer_markdown = (
            f"Question: {question}\n\n"
            "Direct Local Evidence\n"
            "No direct local evidence was found in the current index.\n\n"
            "Model Inference\n"
            "A stronger answer is not justified from the local knowledge base alone."
        )
        return {
            **payload,
            "question": question,
            "answer_markdown": answer_markdown,
            "citations": [],
            "uncertainty": ["No direct local evidence was found."],
        }

    citations = []
    evidence_lines = []
    for index, hit in enumerate(hits[: min(len(hits), 5)], start=1):
        locator = f" ({hit['locator']})" if hit.get("locator") else ""
        source_label = hit["source"]
        if hit.get("library_name"):
            source_label = f"{source_label}:{hit['library_name']}"
        evidence_lines.append(f"{index}. {hit['title']}{locator} [{source_label}]")
        evidence_lines.append(f"   {hit['snippet']}")
        citations.append(
            {
                "title": hit["title"],
                "path": hit["path"],
                "locator": hit.get("locator", ""),
                "source": hit["source"],
                "score": hit["score"],
            }
        )

    top_titles = "; ".join(dict.fromkeys(hit["title"] for hit in hits[:3] if hit.get("title")))
    model_inference = (
        "The strongest local evidence clusters around "
        f"{top_titles or 'the retrieved materials'}. "
        "Use the evidence blocks below as the grounded answer surface."
    )
    answer_markdown = (
        f"Question: {question}\n\n"
        "Direct Local Evidence\n"
        + "\n".join(evidence_lines)
        + "\n\nModel Inference\n"
        + model_inference
    )
    return {
        **payload,
        "question": question,
        "answer_markdown": answer_markdown,
        "citations": citations,
        "uncertainty": [],
    }


def build_report_payload(query: str, payload: dict[str, Any], read_top: int) -> dict[str, Any]:
    hits = payload.get("hits", [])
    debug = payload.get("debug") or {}
    mode = payload.get("mode") or "-"
    effective_mode = debug.get("effective_mode")
    lines = [
        f"QUERY: {query}",
        f"TARGET: {payload.get('target')}",
        f"PROFILE: {payload.get('profile')}",
        f"MODE: {mode}",
        f"TOTAL_HITS: {payload.get('total_hits')}",
        "",
        "HITS",
    ]
    if effective_mode and effective_mode != mode:
        lines.insert(4, f"EFFECTIVE_MODE: {effective_mode}")
    if not hits:
        lines.append("No local evidence found.")
    else:
        for index, hit in enumerate(hits[: max(read_top, 1)], start=1):
            lines.append(format_hit_text(hit, index, explain=True))
            lines.append("")
    return {
        **payload,
        "report_markdown": "\n".join(lines).strip(),
    }

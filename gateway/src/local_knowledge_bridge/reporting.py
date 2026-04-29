from __future__ import annotations

from typing import Any


def _basename(path: str) -> str:
    normalized = str(path or "").rstrip("\\/")
    if not normalized:
        return ""
    return normalized.replace("\\", "/").rsplit("/", 1)[-1]


def _source_path(hit: dict[str, Any]) -> str:
    return str(hit.get("full_path") or hit.get("path") or "")


def _source_file_name(hit: dict[str, Any]) -> str:
    return _basename(_source_path(hit)) or _basename(str(hit.get("path") or "")) or str(hit.get("title") or "")


def _is_literature(hit: dict[str, Any]) -> bool:
    return str(hit.get("source") or "").lower() in {"endnote", "zotero"} or bool(hit.get("doi"))


def _source_key(hit: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(hit.get("source") or ""),
        str(hit.get("canonical_key") or ""),
        _source_path(hit),
        str(hit.get("title") or ""),
    )


def citation_from_hit(hit: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": hit.get("title", ""),
        "doi": hit.get("doi", ""),
        "path": hit.get("path", ""),
        "full_path": hit.get("full_path", ""),
        "file_name": _source_file_name(hit),
        "locator": hit.get("locator", ""),
        "source": hit.get("source", ""),
        "route": hit.get("route", ""),
        "year": hit.get("year", ""),
        "canonical_key": hit.get("canonical_key", ""),
        "library_name": hit.get("library_name", ""),
        "score": hit.get("score", 0.0),
    }


def format_data_sources(hits: list[dict[str, Any]]) -> str:
    seen: set[tuple[str, str, str, str]] = set()
    literature: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    for hit in hits:
        key = _source_key(hit)
        if key in seen:
            continue
        seen.add(key)
        if _is_literature(hit):
            literature.append(hit)
        else:
            documents.append(hit)

    lines = ["DATA SOURCES"]
    if not literature and not documents:
        lines.append("No local data sources found.")
        return "\n".join(lines)

    if literature:
        lines.append("Literature")
        for index, hit in enumerate(literature, start=1):
            lines.append(f"{index}. Title: {hit.get('title') or '-'}")
            lines.append(f"   DOI: {hit.get('doi') or '-'}")
            lines.append(f"   Path: {_source_path(hit) or '-'}")
            if hit.get("locator"):
                lines.append(f"   Locator: {hit['locator']}")
            if hit.get("library_name"):
                lines.append(f"   Library: {hit['library_name']}")
            lines.append(f"   Source: {hit.get('source') or '-'}")

    if documents:
        lines.append("Documents")
        for index, hit in enumerate(documents, start=1):
            lines.append(f"{index}. File: {_source_file_name(hit) or '-'}")
            lines.append(f"   Path: {_source_path(hit) or '-'}")
            if hit.get("locator"):
                lines.append(f"   Locator: {hit['locator']}")
            if hit.get("title"):
                lines.append(f"   Title: {hit['title']}")
            lines.append(f"   Source: {hit.get('source') or '-'}")

    return "\n".join(lines)


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
        lines.append(f"    semantic_score={hit.get('semantic_score', 0.0):.6f}")
        lines.append(f"    rerank_score={hit.get('rerank_score', 0.0):.6f}")
        lines.append(f"    canonical_key={hit['canonical_key']}")
    return "\n".join(lines)


def search_results_text(payload: dict[str, Any], explain: bool = False) -> str:
    if not payload.get("hits"):
        return (
            f"No local results found for query: {payload.get('query', '')}\n\n"
            + format_data_sources([])
        )
    results = "\n\n".join(
        format_hit_text(hit, index, explain=explain)
        for index, hit in enumerate(payload["hits"], start=1)
    )
    return results + "\n\n" + format_data_sources(payload["hits"])


def build_answer_payload(question: str, payload: dict[str, Any]) -> dict[str, Any]:
    hits = payload.get("hits", [])
    if not hits:
        answer_markdown = (
            f"Question: {question}\n\n"
            "Direct Local Evidence\n"
            "No direct local evidence was found in the current index.\n\n"
            "Model Inference\n"
            "A stronger answer is not justified from the local knowledge base alone.\n\n"
            + format_data_sources([])
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
    evidence_hits = hits[: min(len(hits), 5)]
    for index, hit in enumerate(evidence_hits, start=1):
        locator = f" ({hit['locator']})" if hit.get("locator") else ""
        source_label = hit["source"]
        if hit.get("library_name"):
            source_label = f"{source_label}:{hit['library_name']}"
        evidence_lines.append(f"{index}. {hit['title']}{locator} [{source_label}]")
        evidence_lines.append(f"   {hit['snippet']}")
        citations.append(citation_from_hit(hit))

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
        + "\n\n"
        + format_data_sources(evidence_hits)
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
        report_hits = hits[: max(read_top, 1)]
        for index, hit in enumerate(report_hits, start=1):
            lines.append(format_hit_text(hit, index, explain=True))
            lines.append("")
    lines.append("")
    lines.append(format_data_sources(hits[: max(read_top, 1)]))
    return {
        **payload,
        "report_markdown": "\n".join(lines).strip(),
    }

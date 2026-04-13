from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .config import enabled_endnote_libraries, profile_settings, selected_profile
from .constants import SUPPORTED_TARGETS
from .db import connect_index, get_meta, set_meta, table_exists
from .endnote import index_endnote
from .normalize import build_fts_query, make_snippet, parse_year_filters, year_matches_filter
from .obsidian import index_obsidian
from .ranking import fuse_hits
from .schema import clear_index, ensure_schema
from .service_models import SearchHit, SearchRequest
from .source_guard import ensure_gateway_output_path


def _index_db_path(config: dict) -> Path:
    return ensure_gateway_output_path(config.get("index", {}).get("db_path", ""))


def index_status(config: dict) -> dict:
    db_path = _index_db_path(config)
    status = {
        "db_path": str(db_path),
        "exists": db_path.exists(),
        "configured": {
            "obsidian": bool(config.get("obsidian_vault")),
            "endnote": bool(enabled_endnote_libraries(config)),
        },
        "counts": {
            "obsidian_notes": 0,
            "obsidian_chunks": 0,
            "endnote_docs": 0,
            "endnote_attachments": 0,
            "endnote_fulltext": 0,
        },
        "meta": {},
    }
    if not db_path.exists():
        return status

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    try:
        if not table_exists(connection, "index_meta"):
            status["invalid"] = True
            return status
        for table_name in status["counts"]:
            if table_exists(connection, table_name):
                row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
                status["counts"][table_name] = int(row["count"])
        for key in [
            "schema_version",
            "last_build_started_at",
            "last_build_stage",
            "last_build_completed_at",
            "last_build_obsidian_summary",
            "last_build_summary",
        ]:
            value = get_meta(connection, key)
            if value is not None:
                try:
                    status["meta"][key] = json.loads(value)
                except json.JSONDecodeError:
                    status["meta"][key] = value
        return status
    finally:
        connection.close()


def build_index(config: dict, force: bool = False, folder_prefix: str | None = None) -> dict:
    db_path = _index_db_path(config)
    connection = connect_index(db_path)
    try:
        ensure_schema(connection)
        clear_index(connection)
        started_at = time.time()
        set_meta(connection, "last_build_started_at", started_at)
        set_meta(connection, "last_build_stage", "obsidian")
        connection.commit()

        obsidian_summary = index_obsidian(connection, config, folder_prefix=folder_prefix)
        set_meta(connection, "last_build_stage", "endnote")
        set_meta(connection, "last_build_obsidian_summary", obsidian_summary)
        connection.commit()
        endnote_summary = index_endnote(connection, config)

        summary = {
            "db_path": str(db_path),
            "force": bool(force),
            "obsidian": obsidian_summary,
            "endnote": endnote_summary,
            "started_at": started_at,
            "completed_at": time.time(),
        }
        set_meta(connection, "last_build_stage", "completed")
        set_meta(connection, "last_build_summary", summary)
        set_meta(connection, "last_build_completed_at", summary["completed_at"])
        connection.commit()
        return summary
    finally:
        connection.close()


def ensure_index_ready(config: dict, refresh_now: bool = False, auto_refresh: bool = False) -> None:
    db_path = _index_db_path(config)
    if refresh_now or not db_path.exists() or (auto_refresh or bool(config.get("index", {}).get("auto_refresh"))):
        build_index(config, force=refresh_now)


def _build_hit(row: sqlite3.Row, route: str, source: str, query: str) -> SearchHit:
    lexical_score = -float(row["bm25_score"])
    return SearchHit(
        source=source,
        route=route,
        title=str(row["title"] or ""),
        path=str(row["path"] or ""),
        locator=str(row["locator"] or ""),
        snippet=make_snippet(str(row["content_text"] or ""), query),
        year=str(row["year"] or ""),
        doi=str(row["doi"] or ""),
        canonical_key=str(row["canonical_key"] or ""),
        full_path=str(row["full_path"] or ""),
        lexical_score=lexical_score,
        library_id=str(row["library_id"] or ""),
        library_name=str(row["library_name"] or ""),
        extra={"hit_key": str(row["hit_key"] or "")},
    )


def _apply_common_filters(
    hits: list[SearchHit],
    *,
    folder: str | None,
    years: list[tuple[int, int]],
    endnote_library: str | None,
) -> list[SearchHit]:
    filtered: list[SearchHit] = []
    normalized_folder = folder.replace("\\", "/").strip("/") if folder else None
    selector = endnote_library.lower() if endnote_library else None
    for hit in hits:
        if normalized_folder and hit.source == "obsidian" and not hit.path.startswith(normalized_folder):
            continue
        if selector and hit.source == "endnote":
            if selector not in {hit.library_id.lower(), hit.library_name.lower(), hit.full_path.lower(), hit.path.lower()}:
                continue
        if not year_matches_filter(hit.year, years):
            continue
        filtered.append(hit)
    return filtered


def _query_route(
    connection: sqlite3.Connection,
    *,
    sql: str,
    fts_query: str,
    raw_query: str,
    candidate_limit: int,
    route: str,
    source: str,
    folder: str | None,
    years: list[tuple[int, int]],
    endnote_library: str | None,
) -> list[SearchHit]:
    rows = connection.execute(sql, (fts_query, candidate_limit)).fetchall()
    hits = [_build_hit(row, route, source, raw_query) for row in rows]
    hits = _apply_common_filters(hits, folder=folder, years=years, endnote_library=endnote_library)
    return hits


def search_local(config: dict, request: SearchRequest) -> dict:
    profile = selected_profile(config, request.profile)
    if profile == "deep":
        raise SystemExit("The deep profile is not implemented in Local Knowledge Bridge V1. Use fast or balanced.")

    target = request.target.lower()
    if target not in SUPPORTED_TARGETS:
        raise SystemExit(f"Unsupported target: {target}")

    ensure_index_ready(config, refresh_now=request.refresh_now, auto_refresh=request.auto_refresh)
    connection = connect_index(_index_db_path(config))
    try:
        ensure_schema(connection)
        settings = profile_settings(config, profile)
        candidate_limit = max(int(settings["top_k_recall"]), max(request.limit, 1) * 6)
        fts_query = build_fts_query(request.query)
        year_filters = parse_year_filters(request.years)

        route_hits: dict[str, list[SearchHit]] = {}
        if target in {"both", "obsidian"}:
            route_hits["obsidian_notes"] = _query_route(
                connection,
                sql="""
                    SELECT
                        n.note_key AS hit_key,
                        n.canonical_key,
                        n.title,
                        n.rel_path AS path,
                        '' AS locator,
                        n.full_path,
                        n.content_text,
                        n.year,
                        n.doi,
                        '' AS library_id,
                        '' AS library_name,
                        bm25(obsidian_note_fts) AS bm25_score
                    FROM obsidian_note_fts
                    JOIN obsidian_notes n ON n.note_key = obsidian_note_fts.note_key
                    WHERE obsidian_note_fts MATCH ?
                    ORDER BY bm25(obsidian_note_fts)
                    LIMIT ?
                """,
                fts_query=fts_query,
                raw_query=request.query,
                candidate_limit=candidate_limit,
                route="obsidian_notes",
                source="obsidian",
                folder=request.folder,
                years=year_filters,
                endnote_library=request.endnote_library,
            )
            route_hits["obsidian_chunks"] = _query_route(
                connection,
                sql="""
                    SELECT
                        c.chunk_key AS hit_key,
                        c.canonical_key,
                        c.title,
                        c.rel_path AS path,
                        c.locator,
                        c.full_path,
                        c.content_text,
                        c.year,
                        c.doi,
                        '' AS library_id,
                        '' AS library_name,
                        bm25(obsidian_chunk_fts) AS bm25_score
                    FROM obsidian_chunk_fts
                    JOIN obsidian_chunks c ON c.chunk_key = obsidian_chunk_fts.chunk_key
                    WHERE obsidian_chunk_fts MATCH ?
                    ORDER BY bm25(obsidian_chunk_fts)
                    LIMIT ?
                """,
                fts_query=fts_query,
                raw_query=request.query,
                candidate_limit=candidate_limit,
                route="obsidian_chunks",
                source="obsidian",
                folder=request.folder,
                years=year_filters,
                endnote_library=request.endnote_library,
            )

        if target in {"both", "endnote"}:
            route_hits["endnote_docs"] = _query_route(
                connection,
                sql="""
                    SELECT
                        d.doc_key AS hit_key,
                        d.canonical_key,
                        d.title,
                        d.title AS path,
                        'metadata' AS locator,
                        d.library_path AS full_path,
                        d.content_text,
                        d.year,
                        d.doi,
                        d.library_id,
                        d.library_name,
                        bm25(endnote_doc_fts) AS bm25_score
                    FROM endnote_doc_fts
                    JOIN endnote_docs d ON d.doc_key = endnote_doc_fts.doc_key
                    WHERE endnote_doc_fts MATCH ?
                    ORDER BY bm25(endnote_doc_fts)
                    LIMIT ?
                """,
                fts_query=fts_query,
                raw_query=request.query,
                candidate_limit=candidate_limit,
                route="endnote_docs",
                source="endnote",
                folder=request.folder,
                years=year_filters,
                endnote_library=request.endnote_library,
            )
            route_hits["endnote_attachments"] = _query_route(
                connection,
                sql="""
                    SELECT
                        a.attachment_key AS hit_key,
                        a.canonical_key,
                        a.title,
                        a.rel_path AS path,
                        'attachment' AS locator,
                        a.full_path,
                        a.rel_path AS content_text,
                        d.year,
                        d.doi,
                        a.library_id,
                        d.library_name,
                        bm25(endnote_attachment_fts) AS bm25_score
                    FROM endnote_attachment_fts
                    JOIN endnote_attachments a ON a.attachment_key = endnote_attachment_fts.attachment_key
                    JOIN endnote_docs d ON d.doc_key = a.doc_key
                    WHERE endnote_attachment_fts MATCH ?
                    ORDER BY bm25(endnote_attachment_fts)
                    LIMIT ?
                """,
                fts_query=fts_query,
                raw_query=request.query,
                candidate_limit=candidate_limit,
                route="endnote_attachments",
                source="endnote",
                folder=request.folder,
                years=year_filters,
                endnote_library=request.endnote_library,
            )
            route_hits["endnote_fulltext"] = _query_route(
                connection,
                sql="""
                    SELECT
                        f.fulltext_key AS hit_key,
                        f.canonical_key,
                        f.title,
                        f.rel_path AS path,
                        f.locator,
                        f.full_path,
                        f.content_text,
                        f.year,
                        f.doi,
                        f.library_id,
                        d.library_name,
                        bm25(endnote_fulltext_fts) AS bm25_score
                    FROM endnote_fulltext_fts
                    JOIN endnote_fulltext f ON f.fulltext_key = endnote_fulltext_fts.fulltext_key
                    JOIN endnote_docs d ON d.doc_key = f.doc_key
                    WHERE endnote_fulltext_fts MATCH ?
                    ORDER BY bm25(endnote_fulltext_fts)
                    LIMIT ?
                """,
                fts_query=fts_query,
                raw_query=request.query,
                candidate_limit=candidate_limit,
                route="endnote_fulltext",
                source="endnote",
                folder=request.folder,
                years=year_filters,
                endnote_library=request.endnote_library,
            )

        all_hits = fuse_hits(route_hits)
        fused_hits = all_hits[: max(request.limit, 1)]
        return {
            "query": request.query,
            "target": target,
            "profile": profile,
            "hits": [hit.to_dict() for hit in fused_hits],
            "total_hits": len(all_hits),
            "debug": {
                "route_counts": {route: len(hits) for route, hits in route_hits.items()},
                "db_path": str(_index_db_path(config)),
                "folder": request.folder,
                "years": request.years,
                "endnote_library": request.endnote_library,
            },
        }
    finally:
        connection.close()

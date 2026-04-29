from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import enabled_folder_libraries
from .document_text import SUPPORTED_DOCUMENT_SUFFIXES, build_document_chunks, is_supported_document_attachment
from .normalize import build_canonical_key, build_search_text, extract_doi, extract_year, make_snippet
from .pdf_text import build_pdf_chunks, extract_pdf_pages
from .source_guard import validate_folder_library


FOLDER_DOCUMENT_SUFFIXES = {".pdf"} | SUPPORTED_DOCUMENT_SUFFIXES


def _parser_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".txt", ".text"}:
        return "text"
    return suffix.lstrip(".")


def _included_extensions(config: dict) -> set[str]:
    raw = config.get("folder", {}).get("include_extensions") or []
    selected = {str(item).lower() for item in raw if str(item).strip()}
    return selected & FOLDER_DOCUMENT_SUFFIXES if selected else set(FOLDER_DOCUMENT_SUFFIXES)


def _is_skipped(path: Path, root: Path, exclude_dirs: set[str]) -> bool:
    if path.name.startswith("~$"):
        return True
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        rel_parts = path.parts
    return any(part in exclude_dirs for part in rel_parts)


def _document_chunks(path: Path, chunk_chars: int) -> list[dict[str, object]]:
    if path.suffix.lower() == ".pdf":
        return build_pdf_chunks(extract_pdf_pages(path), chunk_chars)
    if is_supported_document_attachment(path):
        return build_document_chunks(path, chunk_chars)
    return []


def index_folder(connection: sqlite3.Connection, config: dict) -> dict[str, object]:
    libraries = enabled_folder_libraries(config)
    if not libraries:
        return {"docs": 0, "chunks": 0, "warnings": []}

    include_extensions = _included_extensions(config)
    exclude_dirs = set(config.get("exclude_dirs", []) or [])
    chunk_chars = int(config.get("index", {}).get("folder_chunk_chars", 1600))
    doc_count = 0
    chunk_count = 0
    warnings: list[str] = []

    for library in libraries:
        folder_id = str(library["id"])
        folder_name = str(library["name"])
        root = validate_folder_library(str(library["path"]))
        for path in sorted(root.rglob("*")):
            if not path.is_file() or _is_skipped(path, root, exclude_dirs):
                continue
            suffix = path.suffix.lower()
            if suffix not in include_extensions:
                continue
            rel_path = path.relative_to(root).as_posix()
            parser_type = _parser_type(path)
            title = path.stem
            try:
                chunks = _document_chunks(path, chunk_chars)
            except Exception as exc:
                warnings.append(f"Folder parse failed for {path}: {exc}")
                continue
            if not chunks:
                continue

            content_text = " ".join(str(chunk["content_text"]) for chunk in chunks)
            year = extract_year(title, rel_path, content_text)
            doi = extract_doi(title, rel_path, content_text)
            doc_key = f"{folder_id}:{rel_path}"
            canonical_key = build_canonical_key("folder", title, year, doi, doc_key)
            stat = path.stat()
            body_snippet = make_snippet(content_text, title or rel_path)
            connection.execute(
                """
                INSERT INTO folder_docs(
                    doc_key, folder_id, folder_name, root_path, rel_path, full_path,
                    file_name, parser_type, title, year, doi, canonical_key, body_snippet,
                    file_size, mtime_ns
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_key,
                    folder_id,
                    folder_name,
                    str(root),
                    rel_path,
                    str(path),
                    path.name,
                    parser_type,
                    title,
                    year,
                    doi,
                    canonical_key,
                    body_snippet,
                    int(stat.st_size),
                    int(stat.st_mtime_ns),
                ),
            )
            connection.execute(
                "INSERT INTO folder_doc_fts(doc_key, search_text) VALUES (?, ?)",
                (doc_key, build_search_text([(3, title), (2, rel_path), (1, body_snippet)])),
            )
            doc_count += 1

            for index, chunk in enumerate(chunks, start=1):
                chunk_key = f"{doc_key}:{index}"
                content = str(chunk["content_text"])
                locator = str(chunk["locator"])
                connection.execute(
                    """
                    INSERT INTO folder_chunks(
                        chunk_key, doc_key, folder_id, folder_name, title, locator, rel_path,
                        full_path, parser_type, year, doi, canonical_key, content_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_key,
                        doc_key,
                        folder_id,
                        folder_name,
                        title,
                        locator,
                        rel_path,
                        str(path),
                        parser_type,
                        year,
                        doi,
                        canonical_key,
                        content,
                    ),
                )
                connection.execute(
                    "INSERT INTO folder_chunk_fts(chunk_key, search_text) VALUES (?, ?)",
                    (chunk_key, build_search_text([(3, title), (2, locator), (2, rel_path), (1, content)])),
                )
                chunk_count += 1

            if doc_count % 20 == 0:
                connection.commit()

    return {"docs": doc_count, "chunks": chunk_count, "warnings": warnings}

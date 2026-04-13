from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path

from .config import enabled_endnote_libraries
from .normalize import build_canonical_key, build_search_text, extract_doi, extract_year
from .pdf_text import build_pdf_chunks, extract_pdf_pages
from .source_guard import resolve_endnote_components


REF_COLUMNS = [
    "id",
    "reference_type",
    "author",
    "year",
    "title",
    "secondary_title",
    "keywords",
    "abstract",
    "notes",
    "research_notes",
    "url",
    "electronic_resource_number",
]


def _open_endnote_db(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _resolve_attachment_path(data_dir: Path, pdf_dir: Path, relative_path: str) -> Path:
    raw = Path(relative_path.replace("\\", "/"))
    if raw.is_absolute():
        return raw
    pdf_candidate = pdf_dir / raw
    if pdf_candidate.exists():
        return pdf_candidate
    return data_dir / raw


def _index_pdf_attachment(
    connection: sqlite3.Connection,
    attachment_key: str,
    doc_key: str,
    library_id: str,
    canonical_key: str,
    ref_id: int,
    title: str,
    year: str,
    doi: str,
    rel_path: str,
    full_path: Path,
    chunk_chars: int,
) -> tuple[int, list[str]]:
    warnings: list[str] = []
    chunk_count = 0
    try:
        pages = extract_pdf_pages(full_path)
        chunks = build_pdf_chunks(pages, chunk_chars)
    except Exception as exc:
        warnings.append(f"PDF parse failed for {full_path}: {exc}")
        return 0, warnings

    for chunk_index, chunk in enumerate(chunks, start=1):
        fulltext_key = f"{attachment_key}:{chunk_index}"
        connection.execute(
            """
            INSERT INTO endnote_fulltext(
                fulltext_key, attachment_key, doc_key, library_id, canonical_key, ref_id,
                title, year, doi, rel_path, full_path, locator, page_start, page_end, content_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fulltext_key,
                attachment_key,
                doc_key,
                library_id,
                canonical_key,
                ref_id,
                title,
                year,
                doi,
                rel_path,
                str(full_path),
                str(chunk["locator"]),
                int(chunk["page_start"]),
                int(chunk["page_end"]),
                str(chunk["content_text"]),
            ),
        )
        search_text = build_search_text(
            [
                (3, title),
                (2, doi),
                (2, str(chunk["locator"])),
                (1, rel_path),
                (1, str(chunk["content_text"])),
            ]
        )
        connection.execute(
            "INSERT INTO endnote_fulltext_fts(fulltext_key, search_text) VALUES (?, ?)",
            (fulltext_key, search_text),
        )
        chunk_count += 1
    return chunk_count, warnings


def index_endnote(connection: sqlite3.Connection, config: dict, selector: str | None = None) -> dict[str, object]:
    libraries = enabled_endnote_libraries(config, selector)
    if not libraries:
        return {"docs": 0, "attachments": 0, "fulltext_chunks": 0, "warnings": []}

    chunk_chars = int(config.get("index", {}).get("endnote_chunk_chars", 1800))
    doc_count = 0
    attachment_count = 0
    fulltext_count = 0
    warnings: list[str] = []

    for library in libraries:
        components = resolve_endnote_components(library["path"])
        library_id = library["id"]
        library_name = library["name"]
        data_dir = Path(components["data_dir"])
        pdf_dir = Path(components["pdf_dir"])
        layout = str(components["layout"])

        if layout == "pdf_only":
            if not pdf_dir.exists():
                warnings.append(f"No readable PDF directory found for EndNote library: {library['path']}")
                continue
            for pdf_path in pdf_dir.rglob("*.pdf"):
                rel_path = pdf_path.relative_to(data_dir).as_posix()
                title = pdf_path.stem
                doc_key = f"{library_id}:pdf:{rel_path}"
                canonical_key = build_canonical_key("endnote", title, "", "", doc_key)
                connection.execute(
                    """
                    INSERT INTO endnote_docs(
                        doc_key, library_id, library_name, library_path, ref_id, canonical_key,
                        reference_type, title, author, year, doi, secondary_title, keywords,
                        abstract_text, notes, research_notes, url, electronic_resource_number, content_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc_key,
                        library_id,
                        library_name,
                        library["path"],
                        0,
                        canonical_key,
                        0,
                        title,
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        title,
                    ),
                )
                connection.execute(
                    "INSERT INTO endnote_doc_fts(doc_key, search_text) VALUES (?, ?)",
                    (doc_key, build_search_text([(3, title), (1, rel_path)])),
                )
                attachment_key = f"{doc_key}:0"
                connection.execute(
                    """
                    INSERT INTO endnote_attachments(
                        attachment_key, doc_key, library_id, canonical_key, ref_id, title,
                        rel_path, full_path, file_type, file_pos
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attachment_key,
                        doc_key,
                        library_id,
                        canonical_key,
                        0,
                        title,
                        rel_path,
                        str(pdf_path),
                        1,
                        0,
                    ),
                )
                connection.execute(
                    "INSERT INTO endnote_attachment_fts(attachment_key, search_text) VALUES (?, ?)",
                    (attachment_key, build_search_text([(2, title), (1, rel_path)])),
                )
                doc_count += 1
                attachment_count += 1
                indexed_chunks, chunk_warnings = _index_pdf_attachment(
                    connection,
                    attachment_key,
                    doc_key,
                    library_id,
                    canonical_key,
                    0,
                    title,
                    "",
                    "",
                    rel_path,
                    pdf_path,
                    chunk_chars,
                )
                fulltext_count += indexed_chunks
                warnings.extend(chunk_warnings)
                if doc_count % 10 == 0:
                    connection.commit()
            continue

        db_connection = _open_endnote_db(Path(components["db_path"]))
        attachment_rows = db_connection.execute(
            "SELECT refs_id, file_path, file_type, file_pos FROM file_res ORDER BY refs_id, file_pos"
        ).fetchall()
        attachments_by_ref: dict[int, list[sqlite3.Row]] = defaultdict(list)
        for attachment_row in attachment_rows:
            attachments_by_ref[int(attachment_row["refs_id"])].append(attachment_row)

        query = (
            "SELECT "
            + ", ".join(REF_COLUMNS)
            + " FROM refs WHERE trash_state = 0 ORDER BY id"
        )
        for row in db_connection.execute(query):
            ref_id = int(row["id"])
            title = str(row["title"] or "")
            year = extract_year(str(row["year"] or ""))
            doi = extract_doi(
                str(row["electronic_resource_number"] or ""),
                str(row["url"] or ""),
                str(row["abstract"] or ""),
                str(row["notes"] or ""),
                title,
            )
            doc_key = f"{library_id}:{ref_id}"
            canonical_key = build_canonical_key("endnote", title, year, doi, doc_key)
            content_text = " ".join(
                str(row[column] or "")
                for column in [
                    "title",
                    "author",
                    "secondary_title",
                    "keywords",
                    "abstract",
                    "notes",
                    "research_notes",
                    "url",
                    "electronic_resource_number",
                ]
            )
            connection.execute(
                """
                INSERT INTO endnote_docs(
                    doc_key, library_id, library_name, library_path, ref_id, canonical_key,
                    reference_type, title, author, year, doi, secondary_title, keywords,
                    abstract_text, notes, research_notes, url, electronic_resource_number, content_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_key,
                    library_id,
                    library_name,
                    library["path"],
                    ref_id,
                    canonical_key,
                    int(row["reference_type"] or 0),
                    title,
                    str(row["author"] or ""),
                    year,
                    doi,
                    str(row["secondary_title"] or ""),
                    str(row["keywords"] or ""),
                    str(row["abstract"] or ""),
                    str(row["notes"] or ""),
                    str(row["research_notes"] or ""),
                    str(row["url"] or ""),
                    str(row["electronic_resource_number"] or ""),
                    content_text,
                ),
            )
            doc_search_text = build_search_text(
                [
                    (3, title),
                    (2, str(row["author"] or "")),
                    (2, str(row["secondary_title"] or "")),
                    (2, doi),
                    (2, str(row["keywords"] or "")),
                    (1, str(row["abstract"] or "")),
                    (1, str(row["notes"] or "")),
                    (1, str(row["research_notes"] or "")),
                    (1, str(row["url"] or "")),
                ]
            )
            connection.execute(
                "INSERT INTO endnote_doc_fts(doc_key, search_text) VALUES (?, ?)",
                (doc_key, doc_search_text),
            )
            doc_count += 1

            for attachment in attachments_by_ref.get(ref_id, []):
                raw_rel_path = str(attachment["file_path"] or "")
                full_path = _resolve_attachment_path(data_dir, pdf_dir, raw_rel_path)
                rel_path = full_path.relative_to(data_dir).as_posix() if full_path.exists() and full_path.is_relative_to(data_dir) else raw_rel_path.replace("\\", "/")
                attachment_key = f"{doc_key}:{int(attachment['file_pos'])}:{rel_path}"
                connection.execute(
                    """
                    INSERT INTO endnote_attachments(
                        attachment_key, doc_key, library_id, canonical_key, ref_id, title,
                        rel_path, full_path, file_type, file_pos
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attachment_key,
                        doc_key,
                        library_id,
                        canonical_key,
                        ref_id,
                        title,
                        rel_path,
                        str(full_path),
                        int(attachment["file_type"] or 0),
                        int(attachment["file_pos"] or 0),
                    ),
                )
                attachment_search_text = build_search_text([(2, title), (2, rel_path), (1, str(full_path))])
                connection.execute(
                    "INSERT INTO endnote_attachment_fts(attachment_key, search_text) VALUES (?, ?)",
                    (attachment_key, attachment_search_text),
                )
                attachment_count += 1

                if full_path.exists() and full_path.suffix.lower() == ".pdf":
                    indexed_chunks, chunk_warnings = _index_pdf_attachment(
                        connection,
                        attachment_key,
                        doc_key,
                        library_id,
                        canonical_key,
                        ref_id,
                        title,
                        year,
                        doi,
                        rel_path,
                        full_path,
                        chunk_chars,
                    )
                    fulltext_count += indexed_chunks
                    warnings.extend(chunk_warnings)

            if doc_count % 10 == 0:
                connection.commit()

        db_connection.close()

    return {
        "docs": doc_count,
        "attachments": attachment_count,
        "fulltext_chunks": fulltext_count,
        "warnings": warnings,
    }

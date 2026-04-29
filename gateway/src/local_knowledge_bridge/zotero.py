from __future__ import annotations

import html
import sqlite3
from pathlib import Path
from typing import Any

from .document_text import build_document_chunks, is_supported_document_attachment
from .normalize import (
    build_canonical_key,
    build_search_text,
    extract_doi,
    extract_year,
    normalize_whitespace,
    read_text_best_effort,
)
from .pdf_text import build_pdf_chunks, extract_pdf_pages
from .source_guard import validate_zotero_sqlite


def _open_zotero_db(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    if not _table_exists(connection, table_name):
        return set()
    return {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table_name})")}


def _strip_html(value: str) -> str:
    text = html.unescape(value or "")
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    parts: list[str] = []
    in_tag = False
    for char in text:
        if char == "<":
            in_tag = True
            parts.append(" ")
            continue
        if char == ">":
            in_tag = False
            continue
        if not in_tag:
            parts.append(char)
    return normalize_whitespace("".join(parts))


def _field_values(connection: sqlite3.Connection) -> dict[int, dict[str, str]]:
    values: dict[int, dict[str, str]] = {}
    if not all(_table_exists(connection, name) for name in ["itemData", "itemDataValues", "fields"]):
        return values
    rows = connection.execute(
        """
        SELECT d.itemID, f.fieldName, v.value
        FROM itemData d
        JOIN fields f ON f.fieldID = d.fieldID
        JOIN itemDataValues v ON v.valueID = d.valueID
        """
    ).fetchall()
    for row in rows:
        item_id = int(row["itemID"])
        values.setdefault(item_id, {})[str(row["fieldName"])] = str(row["value"] or "")
    return values


def _creators_by_item(connection: sqlite3.Connection) -> dict[int, str]:
    if not all(_table_exists(connection, name) for name in ["itemCreators", "creators"]):
        return {}
    rows = connection.execute(
        """
        SELECT ic.itemID, COALESCE(c.lastName, '') AS lastName, COALESCE(c.firstName, '') AS firstName
        FROM itemCreators ic
        JOIN creators c ON c.creatorID = ic.creatorID
        ORDER BY ic.itemID, COALESCE(ic.orderIndex, 0)
        """
    ).fetchall()
    creators: dict[int, list[str]] = {}
    for row in rows:
        name = normalize_whitespace(f"{row['firstName']} {row['lastName']}")
        if name:
            creators.setdefault(int(row["itemID"]), []).append(name)
    return {item_id: "; ".join(names) for item_id, names in creators.items()}


def _attachment_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_exists(connection, "itemAttachments"):
        return []
    attachment_columns = _columns(connection, "itemAttachments")
    item_columns = _columns(connection, "items")
    title_expr = "''"
    if "title" in attachment_columns:
        title_expr = "COALESCE(a.title, '')"
    content_type_expr = "''"
    if "contentType" in attachment_columns:
        content_type_expr = "COALESCE(a.contentType, '')"
    path_expr = "''"
    if "path" in attachment_columns:
        path_expr = "COALESCE(a.path, '')"
    parent_expr = "NULL"
    if "parentItemID" in attachment_columns:
        parent_expr = "a.parentItemID"
    key_expr = "''"
    if "key" in item_columns:
        key_expr = "COALESCE(i.key, '')"
    rows = connection.execute(
        f"""
        SELECT a.itemID, {parent_expr} AS parentItemID, {path_expr} AS path,
               {content_type_expr} AS contentType, {title_expr} AS title, {key_expr} AS itemKey
        FROM itemAttachments a
        LEFT JOIN items i ON i.itemID = a.itemID
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _child_item_ids(connection: sqlite3.Connection, attachments: list[dict[str, Any]]) -> set[int]:
    children = {int(row["itemID"]) for row in attachments if row.get("itemID") is not None}
    for table_name in ["itemNotes", "itemAnnotations"]:
        if _table_exists(connection, table_name) and "itemID" in _columns(connection, table_name):
            children.update(int(row["itemID"]) for row in connection.execute(f"SELECT itemID FROM {table_name}"))
    return children


def _doc_rows(connection: sqlite3.Connection, child_ids: set[int]) -> list[sqlite3.Row]:
    item_type_expr = "''"
    join_item_types = ""
    if _table_exists(connection, "itemTypes") and "itemTypeID" in _columns(connection, "items"):
        item_type_expr = "COALESCE(t.typeName, '')"
        join_item_types = "LEFT JOIN itemTypes t ON t.itemTypeID = i.itemTypeID"
    key_expr = "CAST(i.itemID AS TEXT)"
    if "key" in _columns(connection, "items"):
        key_expr = "COALESCE(i.key, CAST(i.itemID AS TEXT))"
    rows = connection.execute(
        f"""
        SELECT i.itemID, {key_expr} AS itemKey, {item_type_expr} AS itemType
        FROM items i
        {join_item_types}
        ORDER BY i.itemID
        """
    ).fetchall()
    return [row for row in rows if int(row["itemID"]) not in child_ids]


def _insert_doc(
    connection: sqlite3.Connection,
    *,
    doc_key: str,
    item_id: int,
    item_key: str,
    canonical_key: str,
    title: str,
    authors: str,
    year: str,
    doi: str,
    item_type: str,
    abstract: str,
    content_text: str,
    sqlite_mtime_ns: int,
) -> None:
    connection.execute(
        """
        INSERT INTO zotero_docs(
            doc_key, item_id, item_key, canonical_key, title, author, year, doi,
            item_type, abstract_text, content_text, sqlite_mtime_ns
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_key,
            item_id,
            item_key,
            canonical_key,
            title,
            authors,
            year,
            doi,
            item_type,
            abstract,
            content_text,
            sqlite_mtime_ns,
        ),
    )
    connection.execute(
        "INSERT INTO zotero_doc_fts(doc_key, search_text) VALUES (?, ?)",
        (doc_key, build_search_text([(3, title), (2, authors), (2, doi), (1, abstract)])),
    )


def _insert_evidence(
    connection: sqlite3.Connection,
    *,
    evidence_key: str,
    doc_key: str,
    item_id: int,
    item_key: str,
    layer: str,
    title: str,
    locator: str,
    year: str,
    doi: str,
    full_path: str,
    content_text: str,
    comment_text: str,
    canonical_key: str,
) -> None:
    connection.execute(
        """
        INSERT INTO zotero_evidence(
            evidence_key, doc_key, item_id, item_key, layer, title, locator, year, doi,
            full_path, content_text, comment_text, canonical_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            evidence_key,
            doc_key,
            item_id,
            item_key,
            layer,
            title,
            locator,
            year,
            doi,
            full_path,
            content_text,
            comment_text,
            canonical_key,
        ),
    )
    connection.execute(
        "INSERT INTO zotero_evidence_fts(evidence_key, search_text) VALUES (?, ?)",
        (
            evidence_key,
            build_search_text([(3, title), (2, locator), (1, content_text), (1, comment_text)]),
        ),
    )


def _note_rows(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    if not _table_exists(connection, "itemNotes"):
        return []
    columns = _columns(connection, "itemNotes")
    parent_expr = "NULL" if "parentItemID" not in columns else "parentItemID"
    note_expr = "''" if "note" not in columns else "COALESCE(note, '')"
    title_expr = "''" if "title" not in columns else "COALESCE(title, '')"
    return connection.execute(
        f"SELECT itemID, {parent_expr} AS parentItemID, {note_expr} AS note, {title_expr} AS title FROM itemNotes"
    ).fetchall()


def _annotation_rows(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    if not _table_exists(connection, "itemAnnotations"):
        return []
    columns = _columns(connection, "itemAnnotations")
    parent_expr = "NULL" if "parentItemID" not in columns else "parentItemID"
    text_expr = "''" if "text" not in columns else "COALESCE(text, '')"
    comment_expr = "''" if "comment" not in columns else "COALESCE(comment, '')"
    page_expr = "''" if "pageLabel" not in columns else "COALESCE(pageLabel, '')"
    color_expr = "''" if "color" not in columns else "COALESCE(color, '')"
    return connection.execute(
        f"""
        SELECT itemID, {parent_expr} AS parentItemID, {text_expr} AS text,
               {comment_expr} AS comment, {page_expr} AS pageLabel, {color_expr} AS color
        FROM itemAnnotations
        """
    ).fetchall()


def _resolve_attachment_file(storage_root: Path, row: dict[str, Any]) -> Path | None:
    raw_path = str(row.get("path") or "")
    if not raw_path:
        return None
    if raw_path.lower().startswith("storage:"):
        file_name = raw_path.split(":", 1)[1].replace("\\", "/").strip("/")
        item_key = str(row.get("itemKey") or "")
        if not item_key:
            return None
        return storage_root / item_key / file_name
    candidate = Path(raw_path)
    return candidate if candidate.is_absolute() else None


def _attachment_chunks(path: Path, chunk_chars: int) -> list[dict[str, object]]:
    if path.suffix.lower() == ".pdf":
        return build_pdf_chunks(extract_pdf_pages(path), chunk_chars)
    if is_supported_document_attachment(path):
        return build_document_chunks(path, chunk_chars)
    return []


def _attachment_text_layers(
    storage_root: Path,
    row: dict[str, Any],
    chunk_chars: int,
) -> tuple[Path | None, list[tuple[str, list[dict[str, object]]]], str | None]:
    file_path = _resolve_attachment_file(storage_root, row)
    item_key = str(row.get("itemKey") or "")
    cache_path = storage_root / item_key / ".zotero-ft-cache" if item_key else None
    if cache_path and cache_path.exists():
        text = read_text_best_effort(cache_path)
        chunks = [
            {"locator": chunk["locator"], "page_start": 0, "page_end": 0, "content_text": chunk["content_text"]}
            for chunk in build_document_chunks(cache_path, chunk_chars)
        ] if is_supported_document_attachment(cache_path) else []
        if not chunks:
            from .chunking import split_text_chunks

            chunks = [
                {"locator": f"cache [{idx}]" if idx > 1 else "cache", "page_start": 0, "page_end": 0, "content_text": part}
                for idx, part in enumerate(split_text_chunks(text, chunk_chars), start=1)
            ]
        return file_path, [("fulltext", chunks)], None
    if file_path is None or not file_path.exists():
        return file_path, [], f"Zotero attachment not found: {row.get('path')}"
    try:
        chunks = _attachment_chunks(file_path, chunk_chars)
    except Exception as exc:
        return file_path, [], f"Zotero attachment parse failed for {file_path}: {exc}"
    if not chunks:
        return file_path, [], None
    layer = "fulltext" if file_path.suffix.lower() == ".pdf" else "attachment"
    return file_path, [(layer, chunks)], None


def index_zotero(connection: sqlite3.Connection, config: dict) -> dict[str, object]:
    sqlite_value = str(config.get("zotero_sqlite") or "").strip()
    if not sqlite_value:
        return {"docs": 0, "notes": 0, "annotations": 0, "fulltext": 0, "attachments": 0, "warnings": []}

    db_path = validate_zotero_sqlite(sqlite_value)
    storage_root = db_path.parent / "storage"
    sqlite_mtime_ns = int(db_path.stat().st_mtime_ns)
    chunk_chars = int(config.get("index", {}).get("zotero_chunk_chars", 1800))
    warnings: list[str] = []

    zconn = _open_zotero_db(db_path)
    try:
        fields = _field_values(zconn)
        creators = _creators_by_item(zconn)
        attachments = _attachment_rows(zconn)
        child_ids = _child_item_ids(zconn, attachments)
        doc_rows = _doc_rows(zconn, child_ids)
        docs_by_item_id: dict[int, dict[str, str]] = {}
        docs_by_attachment_id: dict[int, dict[str, str]] = {}
        doc_count = 0
        note_count = 0
        annotation_count = 0
        fulltext_count = 0
        attachment_count = 0

        for row in doc_rows:
            item_id = int(row["itemID"])
            item_key = str(row["itemKey"] or item_id)
            values = fields.get(item_id, {})
            title = normalize_whitespace(values.get("title") or values.get("shortTitle") or "(untitled)")
            abstract = _strip_html(values.get("abstractNote") or "")
            authors = creators.get(item_id, "")
            year = extract_year(values.get("date"), values.get("year"), title, abstract)
            doi = extract_doi(values.get("DOI"), values.get("doi"), abstract, title)
            item_type = str(row["itemType"] or "")
            doc_key = f"zotero:{item_id}"
            canonical_key = build_canonical_key("zotero", title, year, doi, doc_key)
            content_text = " ".join([title, authors, year, doi, item_type, abstract])
            _insert_doc(
                connection,
                doc_key=doc_key,
                item_id=item_id,
                item_key=item_key,
                canonical_key=canonical_key,
                title=title,
                authors=authors,
                year=year,
                doi=doi,
                item_type=item_type,
                abstract=abstract,
                content_text=content_text,
                sqlite_mtime_ns=sqlite_mtime_ns,
            )
            docs_by_item_id[item_id] = {
                "doc_key": doc_key,
                "item_key": item_key,
                "title": title,
                "year": year,
                "doi": doi,
                "canonical_key": canonical_key,
            }
            doc_count += 1

        for row in attachments:
            parent_id = row.get("parentItemID")
            if parent_id is not None and int(parent_id) in docs_by_item_id:
                docs_by_attachment_id[int(row["itemID"])] = docs_by_item_id[int(parent_id)]

        for row in _note_rows(zconn):
            parent_id = row["parentItemID"]
            if parent_id is None or int(parent_id) not in docs_by_item_id:
                continue
            doc = docs_by_item_id[int(parent_id)]
            note_text = _strip_html(str(row["note"] or ""))
            if not note_text:
                continue
            title = normalize_whitespace(str(row["title"] or "")) or doc["title"]
            _insert_evidence(
                connection,
                evidence_key=f"zotero-note:{row['itemID']}",
                doc_key=doc["doc_key"],
                item_id=int(parent_id),
                item_key=doc["item_key"],
                layer="note",
                title=title,
                locator="note",
                year=doc["year"],
                doi=doc["doi"],
                full_path="",
                content_text=note_text,
                comment_text="",
                canonical_key=doc["canonical_key"],
            )
            note_count += 1

        for row in _annotation_rows(zconn):
            parent_id = row["parentItemID"]
            if parent_id is None or int(parent_id) not in docs_by_attachment_id:
                continue
            doc = docs_by_attachment_id[int(parent_id)]
            text = normalize_whitespace(str(row["text"] or ""))
            comment = normalize_whitespace(str(row["comment"] or ""))
            if not text and not comment:
                continue
            locator = f"p. {row['pageLabel']}" if row["pageLabel"] else "annotation"
            _insert_evidence(
                connection,
                evidence_key=f"zotero-annotation:{row['itemID']}",
                doc_key=doc["doc_key"],
                item_id=int(parent_id),
                item_key=doc["item_key"],
                layer="annotation",
                title=doc["title"],
                locator=locator,
                year=doc["year"],
                doi=doc["doi"],
                full_path="",
                content_text=text,
                comment_text=comment,
                canonical_key=doc["canonical_key"],
            )
            annotation_count += 1

        for row in attachments:
            parent_id = row.get("parentItemID")
            if parent_id is None or int(parent_id) not in docs_by_item_id:
                continue
            doc = docs_by_item_id[int(parent_id)]
            file_path, layers, warning = _attachment_text_layers(storage_root, row, chunk_chars)
            if warning:
                warnings.append(warning)
            for layer, chunks in layers:
                for index, chunk in enumerate(chunks, start=1):
                    evidence_key = f"zotero-{layer}:{row['itemID']}:{index}"
                    _insert_evidence(
                        connection,
                        evidence_key=evidence_key,
                        doc_key=doc["doc_key"],
                        item_id=int(parent_id),
                        item_key=doc["item_key"],
                        layer=layer,
                        title=doc["title"],
                        locator=str(chunk["locator"]),
                        year=doc["year"],
                        doi=doc["doi"],
                        full_path=str(file_path or ""),
                        content_text=str(chunk["content_text"]),
                        comment_text="",
                        canonical_key=doc["canonical_key"],
                    )
                    if layer == "attachment":
                        attachment_count += 1
                    else:
                        fulltext_count += 1

        return {
            "docs": doc_count,
            "notes": note_count,
            "annotations": annotation_count,
            "fulltext": fulltext_count,
            "attachments": attachment_count,
            "warnings": warnings,
        }
    finally:
        zconn.close()

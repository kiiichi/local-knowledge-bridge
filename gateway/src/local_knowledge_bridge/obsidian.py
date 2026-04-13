from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .chunking import split_markdown_sections, split_text_chunks, strip_frontmatter
from .normalize import (
    build_canonical_key,
    build_search_text,
    extract_doi,
    extract_year,
    read_text_best_effort,
)
from .source_guard import validate_obsidian_vault


def _note_title(metadata: dict[str, str], body: str, path: Path) -> str:
    for key in ["title", "shorttitle", "short_title"]:
        if metadata.get(key):
            return metadata[key]
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path.stem


def _should_skip(rel_path: Path, exclude_dirs: set[str], folder_prefix: str | None) -> bool:
    if any(part in exclude_dirs for part in rel_path.parts[:-1]):
        return True
    if folder_prefix:
        normalized_prefix = folder_prefix.replace("\\", "/").strip("/")
        return not rel_path.as_posix().startswith(normalized_prefix)
    return False


def index_obsidian(
    connection: sqlite3.Connection,
    config: dict,
    folder_prefix: str | None = None,
) -> dict[str, int]:
    vault_value = config.get("obsidian_vault", "")
    if not vault_value:
        return {"notes": 0, "chunks": 0}

    vault = validate_obsidian_vault(vault_value)
    exclude_dirs = {str(item) for item in config.get("exclude_dirs", [])}
    chunk_chars = int(config.get("index", {}).get("obsidian_chunk_chars", 1400))

    note_count = 0
    chunk_count = 0

    for file_path in vault.rglob("*.md"):
        rel_path = file_path.relative_to(vault)
        if _should_skip(rel_path, exclude_dirs, folder_prefix):
            continue

        raw_text = read_text_best_effort(file_path)
        metadata, body = strip_frontmatter(raw_text)
        title = _note_title(metadata, body, file_path)
        doi = extract_doi(metadata.get("doi"), metadata.get("DOI"), body)
        year = extract_year(
            metadata.get("year"),
            metadata.get("datey"),
            metadata.get("date"),
            metadata.get("abstractnote"),
            title,
        )
        note_key = rel_path.as_posix()
        canonical_key = build_canonical_key("obsidian", title, year, doi, note_key)
        content_text = body.strip()
        search_text = build_search_text(
            [
                (3, title),
                (2, note_key),
                (2, doi),
                (1, " ".join(f"{key} {value}" for key, value in metadata.items())),
                (1, content_text),
            ]
        )

        connection.execute(
            """
            INSERT INTO obsidian_notes(
                note_key, canonical_key, title, rel_path, full_path, folder, doi, year,
                metadata_json, content_text, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                note_key,
                canonical_key,
                title,
                note_key,
                str(file_path),
                rel_path.parent.as_posix(),
                doi,
                year,
                json.dumps(metadata, ensure_ascii=False),
                content_text,
                file_path.stat().st_mtime,
            ),
        )
        connection.execute(
            "INSERT INTO obsidian_note_fts(note_key, search_text) VALUES (?, ?)",
            (note_key, search_text),
        )
        note_count += 1

        sections = split_markdown_sections(body, title)
        for section_index, section in enumerate(sections, start=1):
            chunk_parts = split_text_chunks(section["content"], chunk_chars)
            for chunk_index, chunk_text in enumerate(chunk_parts, start=1):
                chunk_key = f"{note_key}#{section_index}.{chunk_index}"
                locator = section["heading"]
                if len(chunk_parts) > 1:
                    locator = f"{locator} [{chunk_index}]"
                chunk_search_text = build_search_text(
                    [
                        (3, title),
                        (2, section["heading"]),
                        (2, doi),
                        (1, note_key),
                        (1, chunk_text),
                    ]
                )
                connection.execute(
                    """
                    INSERT INTO obsidian_chunks(
                        chunk_key, note_key, canonical_key, title, heading, locator,
                        rel_path, full_path, doi, year, content_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_key,
                        note_key,
                        canonical_key,
                        title,
                        section["heading"],
                        locator,
                        note_key,
                        str(file_path),
                        doi,
                        year,
                        chunk_text,
                    ),
                )
                connection.execute(
                    "INSERT INTO obsidian_chunk_fts(chunk_key, search_text) VALUES (?, ?)",
                    (chunk_key, chunk_search_text),
                )
                chunk_count += 1

        if note_count % 25 == 0:
            connection.commit()

    return {"notes": note_count, "chunks": chunk_count}

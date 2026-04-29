from __future__ import annotations

import sqlite3

from .constants import SCHEMA_VERSION
from .db import set_meta


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS index_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS obsidian_notes(
            note_key TEXT PRIMARY KEY,
            canonical_key TEXT NOT NULL,
            title TEXT NOT NULL,
            rel_path TEXT NOT NULL,
            full_path TEXT NOT NULL,
            folder TEXT NOT NULL,
            doi TEXT NOT NULL DEFAULT '',
            year TEXT NOT NULL DEFAULT '',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            content_text TEXT NOT NULL DEFAULT '',
            updated_at REAL NOT NULL DEFAULT 0
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS obsidian_note_fts USING fts5(
            note_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS obsidian_chunks(
            chunk_key TEXT PRIMARY KEY,
            note_key TEXT NOT NULL,
            canonical_key TEXT NOT NULL,
            title TEXT NOT NULL,
            heading TEXT NOT NULL,
            locator TEXT NOT NULL,
            rel_path TEXT NOT NULL,
            full_path TEXT NOT NULL,
            doi TEXT NOT NULL DEFAULT '',
            year TEXT NOT NULL DEFAULT '',
            content_text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS obsidian_chunk_fts USING fts5(
            chunk_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS endnote_docs(
            doc_key TEXT PRIMARY KEY,
            library_id TEXT NOT NULL,
            library_name TEXT NOT NULL,
            library_path TEXT NOT NULL,
            ref_id INTEGER NOT NULL,
            canonical_key TEXT NOT NULL,
            reference_type INTEGER NOT NULL DEFAULT 0,
            title TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL DEFAULT '',
            year TEXT NOT NULL DEFAULT '',
            doi TEXT NOT NULL DEFAULT '',
            secondary_title TEXT NOT NULL DEFAULT '',
            keywords TEXT NOT NULL DEFAULT '',
            abstract_text TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            research_notes TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            electronic_resource_number TEXT NOT NULL DEFAULT '',
            content_text TEXT NOT NULL DEFAULT ''
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS endnote_doc_fts USING fts5(
            doc_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS endnote_attachments(
            attachment_key TEXT PRIMARY KEY,
            doc_key TEXT NOT NULL,
            library_id TEXT NOT NULL,
            canonical_key TEXT NOT NULL,
            ref_id INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            rel_path TEXT NOT NULL DEFAULT '',
            full_path TEXT NOT NULL DEFAULT '',
            file_type INTEGER NOT NULL DEFAULT 0,
            file_pos INTEGER NOT NULL DEFAULT 0
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS endnote_attachment_fts USING fts5(
            attachment_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS endnote_fulltext(
            fulltext_key TEXT PRIMARY KEY,
            attachment_key TEXT NOT NULL,
            doc_key TEXT NOT NULL,
            library_id TEXT NOT NULL,
            canonical_key TEXT NOT NULL,
            ref_id INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            year TEXT NOT NULL DEFAULT '',
            doi TEXT NOT NULL DEFAULT '',
            rel_path TEXT NOT NULL DEFAULT '',
            full_path TEXT NOT NULL DEFAULT '',
            locator TEXT NOT NULL DEFAULT '',
            page_start INTEGER NOT NULL DEFAULT 0,
            page_end INTEGER NOT NULL DEFAULT 0,
            content_text TEXT NOT NULL DEFAULT ''
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS endnote_fulltext_fts USING fts5(
            fulltext_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS zotero_docs(
            doc_key TEXT PRIMARY KEY,
            item_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            canonical_key TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL DEFAULT '',
            year TEXT NOT NULL DEFAULT '',
            doi TEXT NOT NULL DEFAULT '',
            item_type TEXT NOT NULL DEFAULT '',
            abstract_text TEXT NOT NULL DEFAULT '',
            content_text TEXT NOT NULL DEFAULT '',
            sqlite_mtime_ns INTEGER NOT NULL DEFAULT 0
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS zotero_doc_fts USING fts5(
            doc_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS zotero_evidence(
            evidence_key TEXT PRIMARY KEY,
            doc_key TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            layer TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            locator TEXT NOT NULL DEFAULT '',
            year TEXT NOT NULL DEFAULT '',
            doi TEXT NOT NULL DEFAULT '',
            full_path TEXT NOT NULL DEFAULT '',
            content_text TEXT NOT NULL DEFAULT '',
            comment_text TEXT NOT NULL DEFAULT '',
            canonical_key TEXT NOT NULL DEFAULT ''
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS zotero_evidence_fts USING fts5(
            evidence_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS folder_docs(
            doc_key TEXT PRIMARY KEY,
            folder_id TEXT NOT NULL,
            folder_name TEXT NOT NULL,
            root_path TEXT NOT NULL,
            rel_path TEXT NOT NULL,
            full_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            parser_type TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            year TEXT NOT NULL DEFAULT '',
            doi TEXT NOT NULL DEFAULT '',
            canonical_key TEXT NOT NULL,
            body_snippet TEXT NOT NULL DEFAULT '',
            file_size INTEGER NOT NULL DEFAULT 0,
            mtime_ns INTEGER NOT NULL DEFAULT 0
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS folder_doc_fts USING fts5(
            doc_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TABLE IF NOT EXISTS folder_chunks(
            chunk_key TEXT PRIMARY KEY,
            doc_key TEXT NOT NULL,
            folder_id TEXT NOT NULL,
            folder_name TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            locator TEXT NOT NULL DEFAULT '',
            rel_path TEXT NOT NULL DEFAULT '',
            full_path TEXT NOT NULL DEFAULT '',
            parser_type TEXT NOT NULL DEFAULT '',
            year TEXT NOT NULL DEFAULT '',
            doi TEXT NOT NULL DEFAULT '',
            canonical_key TEXT NOT NULL,
            content_text TEXT NOT NULL DEFAULT ''
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS folder_chunk_fts USING fts5(
            chunk_key UNINDEXED,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )
    set_meta(connection, "schema_version", SCHEMA_VERSION)


def clear_index(connection: sqlite3.Connection) -> None:
    for table_name in [
        "obsidian_note_fts",
        "obsidian_chunk_fts",
        "endnote_doc_fts",
        "endnote_attachment_fts",
        "endnote_fulltext_fts",
        "zotero_doc_fts",
        "zotero_evidence_fts",
        "folder_doc_fts",
        "folder_chunk_fts",
        "obsidian_notes",
        "obsidian_chunks",
        "endnote_docs",
        "endnote_attachments",
        "endnote_fulltext",
        "zotero_docs",
        "zotero_evidence",
        "folder_docs",
        "folder_chunks",
    ]:
        connection.execute(f"DELETE FROM {table_name}")

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .source_guard import ensure_gateway_output_path


def connect_index(db_path: str | Path) -> sqlite3.Connection:
    resolved = ensure_gateway_output_path(db_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(resolved))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA busy_timeout=60000")
    return connection


def get_meta(connection: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = connection.execute("SELECT value FROM index_meta WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return str(row["value"])


def set_meta(connection: sqlite3.Connection, key: str, value: Any) -> None:
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    connection.execute(
        "INSERT INTO index_meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None

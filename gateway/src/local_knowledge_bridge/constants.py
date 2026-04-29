from __future__ import annotations

SCHEMA_VERSION = 2
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 53744
RRF_K = 60
DEFAULT_RELEASE_API_URL = "https://api.github.com/repos/kiiichi/local-knowledge-bridge/releases/latest"
DEFAULT_RELEASE_URL = "https://github.com/kiiichi/local-knowledge-bridge/releases"
DEFAULT_UPDATE_TIMEOUT_SECONDS = 5.0

PROFILE_SETTINGS = {
    "fast": {
        "top_k_recall": 24,
        "top_k_evidence": 5,
        "top_k_report": 8,
        "semantic": False,
    },
    "balanced": {
        "top_k_recall": 40,
        "top_k_evidence": 6,
        "top_k_report": 10,
        "semantic": False,
    },
    "deep": {
        "top_k_recall": 80,
        "top_k_evidence": 8,
        "top_k_report": 12,
        "semantic": True,
    },
}

DEFAULT_ROUTE_WEIGHTS = {
    "obsidian_notes": 1.2,
    "obsidian_chunks": 1.4,
    "endnote_docs": 1.1,
    "endnote_attachments": 0.95,
    "endnote_fulltext": 1.0,
    "zotero_docs": 1.1,
    "zotero_notes": 1.2,
    "zotero_annotations": 1.25,
    "zotero_fulltext": 1.0,
    "zotero_attachments": 0.95,
    "folder_docs": 0.85,
    "folder_chunks": 1.0,
}

DEFAULT_SCORING = {
    "title_hit_cap": 3,
    "text_hit_cap": 12,
    "title_hit_weight": 10.0,
    "text_hit_weight": 2.0,
    "title_contains_bonus": 8.0,
    "expansion_bonus_weight": 0.15,
    "char_ngram_n": 3,
    "char_ngram_weight": 20.0,
    "semantic_char_ngram_weight": 100.0,
    "fts_bonus_base": 40.0,
    "fts_bonus_scale": 4.0,
}

SUPPORTED_TARGETS = {"both", "obsidian", "endnote", "zotero", "folder"}

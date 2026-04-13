from __future__ import annotations

SCHEMA_VERSION = 1
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 53744
RRF_K = 60

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

ROUTE_WEIGHTS = {
    "obsidian_notes": 1.2,
    "obsidian_chunks": 1.4,
    "endnote_docs": 1.1,
    "endnote_attachments": 0.95,
    "endnote_fulltext": 1.0,
}

SUPPORTED_TARGETS = {"both", "obsidian", "endnote"}

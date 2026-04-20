from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DEFAULT_MODE = "hybrid"
SUPPORTED_MODES = frozenset({"lexical", "hybrid", "semantic"})


def normalize_mode(mode: str | None) -> str:
    name = str(mode or DEFAULT_MODE).strip().lower()
    if name not in SUPPORTED_MODES:
        raise SystemExit(f"Unsupported mode: {name}")
    return name


def _search_request_kwargs(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": str(data.get("query", "")),
        "target": str(data.get("target", "both")),
        "profile": str(data.get("profile", "fast")),
        "mode": data.get("mode", DEFAULT_MODE),
        "folder": data.get("folder"),
        "endnote_library": data.get("endnote_library"),
        "years": data.get("years"),
        "limit": int(data.get("limit", 10)),
        "explain": bool(data.get("explain", False)),
        "auto_refresh": bool(data.get("auto_refresh", False)),
        "refresh_now": bool(data.get("refresh_now", False)),
    }


@dataclass
class SearchHit:
    source: str
    route: str
    title: str
    path: str
    locator: str
    snippet: str
    year: str
    doi: str
    canonical_key: str
    full_path: str
    score: float = 0.0
    lexical_score: float = 0.0
    library_id: str = ""
    library_name: str = ""
    routes: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["score"] = round(float(self.score), 6)
        payload["lexical_score"] = round(float(self.lexical_score), 6)
        return payload


@dataclass
class SearchRequest:
    query: str
    target: str = "both"
    profile: str = "fast"
    mode: str = DEFAULT_MODE
    folder: str | None = None
    endnote_library: str | None = None
    years: str | None = None
    limit: int = 10
    explain: bool = False
    auto_refresh: bool = False
    refresh_now: bool = False

    def __post_init__(self) -> None:
        self.mode = normalize_mode(self.mode)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "SearchRequest":
        return cls(**_search_request_kwargs(data))


@dataclass
class AskRequest(SearchRequest):
    question: str = ""

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "AskRequest":
        kwargs = _search_request_kwargs(data)
        question = str(data.get("question", data.get("query", "")))
        kwargs["query"] = kwargs["query"] or question
        return cls(
            question=question,
            **kwargs,
        )


@dataclass
class ReportRequest(SearchRequest):
    read_top: int = 3

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ReportRequest":
        kwargs = _search_request_kwargs(data)
        return cls(
            read_top=int(data.get("read_top", 3)),
            **kwargs,
        )

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


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
    folder: str | None = None
    endnote_library: str | None = None
    years: str | None = None
    limit: int = 10
    explain: bool = False
    auto_refresh: bool = False
    refresh_now: bool = False

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "SearchRequest":
        return cls(
            query=str(data.get("query", "")),
            target=str(data.get("target", "both")),
            profile=str(data.get("profile", "fast")),
            folder=data.get("folder"),
            endnote_library=data.get("endnote_library"),
            years=data.get("years"),
            limit=int(data.get("limit", 10)),
            explain=bool(data.get("explain", False)),
            auto_refresh=bool(data.get("auto_refresh", False)),
            refresh_now=bool(data.get("refresh_now", False)),
        )


@dataclass
class AskRequest(SearchRequest):
    question: str = ""

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "AskRequest":
        base = SearchRequest.from_mapping(data)
        return cls(
            query=base.query or str(data.get("question", "")),
            question=str(data.get("question", data.get("query", ""))),
            target=base.target,
            profile=base.profile,
            folder=base.folder,
            endnote_library=base.endnote_library,
            years=base.years,
            limit=base.limit,
            explain=base.explain,
            auto_refresh=base.auto_refresh,
            refresh_now=base.refresh_now,
        )


@dataclass
class ReportRequest(SearchRequest):
    read_top: int = 3

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ReportRequest":
        base = SearchRequest.from_mapping(data)
        return cls(
            query=base.query,
            target=base.target,
            profile=base.profile,
            folder=base.folder,
            endnote_library=base.endnote_library,
            years=base.years,
            limit=base.limit,
            explain=base.explain,
            auto_refresh=base.auto_refresh,
            refresh_now=base.refresh_now,
            read_top=int(data.get("read_top", 3)),
        )

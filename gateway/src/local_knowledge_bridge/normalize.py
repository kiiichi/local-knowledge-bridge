from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(18|19|20)\d{2}\b")
WORD_RE = re.compile(r"[0-9A-Za-z]+")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_doi(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.strip().strip(".,;)")
    if normalized.lower().startswith("doi:"):
        normalized = normalized[4:]
    return normalized.lower()


def extract_doi(*values: str | None) -> str:
    for value in values:
        if not value:
            continue
        match = DOI_RE.search(value)
        if match:
            return normalize_doi(match.group(0))
    return ""


def extract_year(*values: str | None) -> str:
    for value in values:
        if not value:
            continue
        match = YEAR_RE.search(value)
        if match:
            return match.group(0)
    return ""


def slugify_text(value: str) -> str:
    lowered = normalize_whitespace(value).lower()
    lowered = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "-", lowered)
    return lowered.strip("-")


def build_canonical_key(source: str, title: str, year: str, doi: str, fallback_id: str) -> str:
    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        return f"doi:{normalized_doi}"
    normalized_title = slugify_text(title) or slugify_text(Path(fallback_id).stem) or fallback_id
    if year:
        return f"{source}:{normalized_title}:{year}"
    return f"{source}:{normalized_title}:{fallback_id}"


def lexical_tokens(text: str) -> list[str]:
    normalized = normalize_whitespace(text).lower()
    tokens: list[str] = []
    seen: set[str] = set()
    for match in WORD_RE.finditer(normalized):
        token = match.group(0)
        if token not in seen:
            seen.add(token)
            tokens.append(token)
    for match in CJK_RE.finditer(normalized):
        run = match.group(0)
        grams = [run] if len(run) == 1 else [run[idx : idx + 2] for idx in range(len(run) - 1)]
        for token in grams:
            if token not in seen:
                seen.add(token)
                tokens.append(token)
    return tokens


def build_search_text(weighted_values: Iterable[tuple[int, str]]) -> str:
    expanded: list[str] = []
    for weight, value in weighted_values:
        tokens = lexical_tokens(value)
        for _ in range(max(weight, 1)):
            expanded.extend(tokens)
    return " ".join(expanded)


def build_fts_query(text: str, max_terms: int = 24) -> str:
    tokens = lexical_tokens(text)[:max_terms]
    if not tokens:
        return '""'
    terms: list[str] = []
    for token in tokens:
        escaped = token.replace('"', '""')
        terms.append(f'"{escaped}"')
        if token.isascii() and len(token) >= 3:
            terms.append(f"{escaped}*")
    return " OR ".join(terms)


def make_snippet(text: str, query: str, max_chars: int = 220) -> str:
    source_text = normalize_whitespace(text)
    if not source_text:
        return ""
    lowered = source_text.lower()
    needles = [normalize_whitespace(query).lower()] + lexical_tokens(query)
    index = -1
    needle_len = 0
    for needle in needles:
        if not needle:
            continue
        candidate = lowered.find(needle.lower())
        if candidate >= 0:
            index = candidate
            needle_len = len(needle)
            break
    if index < 0:
        return source_text[:max_chars]
    start = max(index - max_chars // 3, 0)
    end = min(index + needle_len + (max_chars * 2 // 3), len(source_text))
    snippet = source_text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(source_text):
        snippet = snippet + "..."
    return snippet


def read_text_best_effort(path: Path) -> str:
    for encoding in ["utf-8-sig", "utf-8", "gb18030", "cp936", "latin-1"]:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_year_filters(value: str | None) -> list[tuple[int, int]]:
    if not value:
        return []
    ranges: list[tuple[int, int]] = []
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            left, right = token.split("-", 1)
            if left.isdigit() and right.isdigit():
                start = int(left)
                end = int(right)
                ranges.append((min(start, end), max(start, end)))
        elif token.isdigit():
            year = int(token)
            ranges.append((year, year))
    return ranges


def year_matches_filter(year_value: str | None, ranges: list[tuple[int, int]]) -> bool:
    if not ranges:
        return True
    year = extract_year(year_value or "")
    if not year:
        return False
    year_num = int(year)
    return any(start <= year_num <= end for start, end in ranges)

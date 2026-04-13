from __future__ import annotations

import re

from .normalize import normalize_whitespace


def strip_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}, text
    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() in {"---", "..."}:
            end_index = idx
            break
    if end_index is None:
        return {}, text
    yaml_block = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(yaml_block) or {}
        if isinstance(loaded, dict):
            return {str(key): str(value) for key, value in loaded.items() if value is not None}, body
    except Exception:
        pass

    metadata: dict[str, str] = {}
    for line in yaml_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, body


def split_markdown_sections(text: str, fallback_title: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    sections: list[dict[str, str]] = []
    current_heading = fallback_title
    current_lines: list[str] = []

    def flush(heading: str, raw_lines: list[str]) -> None:
        content = normalize_whitespace("\n".join(raw_lines))
        if content:
            sections.append({"heading": heading, "content": content})

    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if match:
            flush(current_heading, current_lines)
            current_heading = normalize_whitespace(match.group(2)) or fallback_title
            current_lines = []
            continue
        current_lines.append(line)

    flush(current_heading, current_lines)
    if not sections:
        content = normalize_whitespace(text)
        if content:
            sections.append({"heading": fallback_title, "content": content})
    return sections


def split_text_chunks(text: str, max_chars: int) -> list[str]:
    normalized = normalize_whitespace(text)
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]

    pieces = re.split(r"(?<=[.!?。！？])\s+", normalized)
    chunks: list[str] = []
    bucket = ""

    for piece in pieces:
        if not piece:
            continue
        if len(piece) > max_chars:
            if bucket:
                chunks.append(bucket.strip())
                bucket = ""
            for start in range(0, len(piece), max_chars):
                chunks.append(piece[start : start + max_chars].strip())
            continue
        candidate = f"{bucket} {piece}".strip() if bucket else piece
        if len(candidate) <= max_chars:
            bucket = candidate
        else:
            if bucket:
                chunks.append(bucket.strip())
            bucket = piece

    if bucket:
        chunks.append(bucket.strip())
    return chunks

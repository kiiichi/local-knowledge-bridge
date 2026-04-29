from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .chunking import split_markdown_sections, split_text_chunks, strip_frontmatter
from .normalize import normalize_whitespace


SUPPORTED_DOCUMENT_SUFFIXES = {
    ".docx",
    ".markdown",
    ".md",
    ".pptx",
    ".text",
    ".txt",
    ".xlsx",
}


def is_supported_document_attachment(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_DOCUMENT_SUFFIXES


def _chunk_plain_text(text: str, max_chars: int, locator_prefix: str) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    for index, content_text in enumerate(split_text_chunks(text, max_chars), start=1):
        locator = locator_prefix if index == 1 else f"{locator_prefix} [{index}]"
        chunks.append(
            {
                "locator": locator,
                "page_start": 0,
                "page_end": 0,
                "content_text": content_text,
            }
        )
    return chunks


def _extract_docx_paragraphs(path: Path) -> list[str]:
    paragraphs: list[str] = []
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    for paragraph in root.findall(".//w:p", namespace):
        pieces = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        text = normalize_whitespace("".join(pieces))
        if text:
            paragraphs.append(text)
    return paragraphs


def _extract_pptx_slides(path: Path) -> list[tuple[str, str]]:
    slides: list[tuple[str, str]] = []
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        slide_names = sorted(
            slide_names,
            key=lambda name: int(match.group(1)) if (match := re.search(r"slide(\d+)\.xml$", name)) else 0,
        )
        for fallback_index, slide_name in enumerate(slide_names, start=1):
            root = ET.fromstring(archive.read(slide_name))
            pieces = [node.text or "" for node in root.findall(".//{*}t")]
            text = normalize_whitespace(" ".join(pieces))
            if not text:
                continue
            match = re.search(r"slide(\d+)\.xml$", slide_name, re.IGNORECASE)
            slide_number = match.group(1) if match else str(fallback_index)
            slides.append((f"slide {slide_number}", text))
    return slides


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for node in root.findall(".//{*}si"):
        text = normalize_whitespace(" ".join(part.text or "" for part in node.findall(".//{*}t")))
        values.append(text)
    return values


def _xlsx_sheet_names(archive: zipfile.ZipFile) -> list[str]:
    if "xl/workbook.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/workbook.xml"))
    names: list[str] = []
    for index, sheet in enumerate(root.findall(".//{*}sheet"), start=1):
        names.append(str(sheet.attrib.get("name") or f"Sheet {index}"))
    return names


def _extract_xlsx_sheets(path: Path) -> list[tuple[str, str]]:
    sheets: list[tuple[str, str]] = []
    with zipfile.ZipFile(path) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        sheet_names = _xlsx_sheet_names(archive)
        worksheet_names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        worksheet_names = sorted(
            worksheet_names,
            key=lambda name: int(match.group(1)) if (match := re.search(r"sheet(\d+)\.xml$", name)) else 0,
        )
        for index, sheet_file in enumerate(worksheet_names, start=1):
            root = ET.fromstring(archive.read(sheet_file))
            rows: list[str] = []
            for row in root.findall(".//{*}row"):
                values: list[str] = []
                for cell in row.findall("{*}c"):
                    cell_type = cell.attrib.get("t")
                    raw_value = ""
                    if cell_type == "inlineStr":
                        raw_value = " ".join(node.text or "" for node in cell.findall(".//{*}t"))
                    else:
                        value_node = cell.find("{*}v")
                        raw_value = value_node.text if value_node is not None and value_node.text else ""
                        if cell_type == "s" and raw_value:
                            try:
                                raw_value = shared_strings[int(raw_value)]
                            except (IndexError, ValueError):
                                pass
                    value = normalize_whitespace(raw_value)
                    if value:
                        values.append(value)
                if values:
                    rows.append(" | ".join(values))
            text = normalize_whitespace(" ".join(rows))
            if text:
                sheet_name = sheet_names[index - 1] if index <= len(sheet_names) else f"Sheet {index}"
                sheets.append((f"sheet {sheet_name}", text))
    return sheets


def build_document_chunks(path: Path, max_chars: int) -> list[dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        metadata, body = strip_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
        fallback_title = metadata.get("title") or path.stem
        chunks: list[dict[str, object]] = []
        for section in split_markdown_sections(body, fallback_title):
            chunks.extend(_chunk_plain_text(section["content"], max_chars, section["heading"]))
        return chunks
    if suffix in {".txt", ".text"}:
        return _chunk_plain_text(path.read_text(encoding="utf-8", errors="ignore"), max_chars, "text")
    if suffix == ".docx":
        return _chunk_plain_text(" ".join(_extract_docx_paragraphs(path)), max_chars, "document")
    if suffix == ".pptx":
        chunks = []
        for locator, text in _extract_pptx_slides(path):
            chunks.extend(_chunk_plain_text(text, max_chars, locator))
        return chunks
    if suffix == ".xlsx":
        chunks = []
        for locator, text in _extract_xlsx_sheets(path):
            chunks.extend(_chunk_plain_text(text, max_chars, locator))
        return chunks
    return []

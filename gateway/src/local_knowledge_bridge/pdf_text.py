from __future__ import annotations

import logging
import warnings
from contextlib import contextmanager
from pathlib import Path

from .chunking import split_text_chunks
from .normalize import normalize_whitespace


@contextmanager
def _quiet_pypdf() -> None:
    logger_names = [
        "pypdf",
        "pypdf._reader",
        "pypdf._page",
        "pypdf._cmap",
        "pypdf._writer",
    ]
    logger_state: list[tuple[logging.Logger, int, bool]] = []
    previous_disable = logging.root.manager.disable
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger_state.append((logger, logger.level, logger.propagate))
        logger.setLevel(logging.ERROR)
        logger.propagate = False

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        logging.disable(logging.CRITICAL)
        try:
            yield
        finally:
            logging.disable(previous_disable)
            for logger, level, propagate in logger_state:
                logger.setLevel(level)
                logger.propagate = propagate


def extract_pdf_pages(pdf_path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pypdf is required for PDF indexing. Run lkb_bootstrap_runtime.cmd first."
        ) from exc

    pages: list[str] = []
    with _quiet_pypdf():
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            try:
                pages.append(normalize_whitespace(page.extract_text() or ""))
            except Exception:
                pages.append("")
    return pages


def build_pdf_chunks(page_texts: list[str], max_chars: int) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    page_index = 0
    while page_index < len(page_texts):
        current_text = page_texts[page_index]
        if not current_text:
            page_index += 1
            continue

        start_page = page_index + 1
        end_page = start_page
        bucket = current_text
        page_index += 1

        while page_index < len(page_texts) and page_texts[page_index]:
            candidate = f"{bucket} {page_texts[page_index]}".strip()
            if len(candidate) > max_chars:
                break
            bucket = candidate
            end_page = page_index + 1
            page_index += 1

        chunk_parts = split_text_chunks(bucket, max_chars)
        for idx, chunk_text in enumerate(chunk_parts, start=1):
            locator = f"p. {start_page}" if start_page == end_page else f"pp. {start_page}-{end_page}"
            if len(chunk_parts) > 1:
                locator = f"{locator} [{idx}]"
            chunks.append(
                {
                    "locator": locator,
                    "page_start": start_page,
                    "page_end": end_page,
                    "content_text": chunk_text,
                }
            )
    return chunks

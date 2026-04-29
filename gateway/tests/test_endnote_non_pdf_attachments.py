from __future__ import annotations

import sqlite3
import sys
import unittest
import zipfile
from pathlib import Path

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(__file__).resolve().parent
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from local_knowledge_bridge.endnote import index_endnote
from local_knowledge_bridge.schema import ensure_schema
from support import scratch_dir


def _write_docx(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>
</w:document>
"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)


def _write_pptx(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>
"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide_xml)


class EndNoteNonPdfAttachmentTests(unittest.TestCase):
    def test_docx_pptx_and_markdown_attachments_are_indexed_as_fulltext(self) -> None:
        with scratch_dir("endnote_non_pdf_attachments") as temp_dir:
            library_path = temp_dir / "Research.enl"
            data_dir = temp_dir / "Research.Data"
            db_path = data_dir / "sdb" / "sdb.eni"
            attachment_dir = data_dir / "PDF"
            db_path.parent.mkdir(parents=True)
            attachment_dir.mkdir(parents=True)
            library_path.write_text("", encoding="utf-8")

            _write_docx(attachment_dir / "methods.docx", "docxneedle interferometry protocol")
            _write_pptx(attachment_dir / "slides.pptx", "pptxneedle calibration slide")
            (attachment_dir / "notes.md").write_text(
                "# Lab Notes\n\nmarkdownneedle alignment observation",
                encoding="utf-8",
            )

            endnote_db = sqlite3.connect(db_path)
            endnote_db.executescript(
                """
                CREATE TABLE refs(
                    id INTEGER PRIMARY KEY,
                    reference_type INTEGER,
                    author TEXT,
                    year TEXT,
                    title TEXT,
                    secondary_title TEXT,
                    keywords TEXT,
                    abstract TEXT,
                    notes TEXT,
                    research_notes TEXT,
                    url TEXT,
                    electronic_resource_number TEXT,
                    trash_state INTEGER
                );
                CREATE TABLE file_res(
                    refs_id INTEGER,
                    file_path TEXT,
                    file_type INTEGER,
                    file_pos INTEGER
                );
                INSERT INTO refs VALUES(
                    1, 17, 'A. Researcher', '2026', 'Non PDF EndNote Attachments',
                    '', '', '', '', '', '', '', 0
                );
                INSERT INTO file_res VALUES(1, 'methods.docx', 1, 1);
                INSERT INTO file_res VALUES(1, 'slides.pptx', 1, 2);
                INSERT INTO file_res VALUES(1, 'notes.md', 1, 3);
                """
            )
            endnote_db.commit()
            endnote_db.close()

            index_db = sqlite3.connect(temp_dir / "index.sqlite")
            index_db.row_factory = sqlite3.Row
            ensure_schema(index_db)
            summary = index_endnote(
                index_db,
                {
                    "endnote_libraries": [
                        {
                            "id": "research",
                            "name": "Research",
                            "path": str(library_path),
                            "enabled": True,
                        }
                    ],
                    "index": {"endnote_chunk_chars": 400},
                },
            )

            self.assertEqual(summary["attachments"], 3)
            self.assertEqual(summary["fulltext_chunks"], 3)
            for term in ["docxneedle", "pptxneedle", "markdownneedle"]:
                row = index_db.execute(
                    "SELECT COUNT(*) AS count FROM endnote_fulltext_fts WHERE endnote_fulltext_fts MATCH ?",
                    (term,),
                ).fetchone()
                self.assertEqual(row["count"], 1, term)
            index_db.close()


if __name__ == "__main__":
    unittest.main()

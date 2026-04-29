from __future__ import annotations

import sqlite3
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(__file__).resolve().parent
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from local_knowledge_bridge.folder import index_folder
from local_knowledge_bridge.retrieval import search_local
from local_knowledge_bridge.schema import ensure_schema
from local_knowledge_bridge.service_models import SearchRequest
from local_knowledge_bridge.zotero import index_zotero
from support import scratch_dir


def _write_docx(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>
</w:document>
""",
        )


def _write_pptx(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "ppt/slides/slide1.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>
""",
        )


def _write_xlsx(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?><workbook><sheets><sheet name="Sheet1"/></sheets></workbook>""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?><worksheet><sheetData><row><c t="inlineStr"><is><t>{text}</t></is></c></row></sheetData></worksheet>""",
        )


class ZoteroSourceTests(unittest.TestCase):
    def test_zotero_metadata_notes_annotations_fulltext_and_attachments_are_indexed(self) -> None:
        with scratch_dir("zotero_source") as temp_dir:
            zotero_path = temp_dir / "zotero.sqlite"
            storage = temp_dir / "storage"
            (storage / "ATT1").mkdir(parents=True)
            (storage / "ATT2").mkdir(parents=True)
            (storage / "ATT1" / ".zotero-ft-cache").write_text("fulltextneedle cached pdf evidence", encoding="utf-8")
            _write_docx(storage / "ATT2" / "supp.docx", "attachmentneedle supplemental evidence")

            zconn = sqlite3.connect(zotero_path)
            zconn.executescript(
                """
                CREATE TABLE items(itemID INTEGER PRIMARY KEY, key TEXT, itemTypeID INTEGER);
                CREATE TABLE itemTypes(itemTypeID INTEGER PRIMARY KEY, typeName TEXT);
                CREATE TABLE fields(fieldID INTEGER PRIMARY KEY, fieldName TEXT);
                CREATE TABLE itemData(itemID INTEGER, fieldID INTEGER, valueID INTEGER);
                CREATE TABLE itemDataValues(valueID INTEGER PRIMARY KEY, value TEXT);
                CREATE TABLE creators(creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT);
                CREATE TABLE itemCreators(itemID INTEGER, creatorID INTEGER, orderIndex INTEGER);
                CREATE TABLE itemNotes(itemID INTEGER, parentItemID INTEGER, note TEXT, title TEXT);
                CREATE TABLE itemAttachments(itemID INTEGER, parentItemID INTEGER, path TEXT, contentType TEXT, title TEXT);
                CREATE TABLE itemAnnotations(itemID INTEGER, parentItemID INTEGER, text TEXT, comment TEXT, pageLabel TEXT, color TEXT);
                INSERT INTO itemTypes VALUES(1, 'journalArticle');
                INSERT INTO items VALUES(1, 'DOC1', 1);
                INSERT INTO items VALUES(2, 'ATT1', 1);
                INSERT INTO items VALUES(3, 'NOTE1', 1);
                INSERT INTO items VALUES(4, 'ANNOT1', 1);
                INSERT INTO items VALUES(5, 'ATT2', 1);
                INSERT INTO items VALUES(6, 'MISS1', 1);
                INSERT INTO fields VALUES(1, 'title');
                INSERT INTO fields VALUES(2, 'date');
                INSERT INTO fields VALUES(3, 'DOI');
                INSERT INTO fields VALUES(4, 'abstractNote');
                INSERT INTO itemDataValues VALUES(1, 'Zotero Test Paper');
                INSERT INTO itemDataValues VALUES(2, '2026');
                INSERT INTO itemDataValues VALUES(3, '10.1000/zotero');
                INSERT INTO itemDataValues VALUES(4, 'metadata summary');
                INSERT INTO itemData VALUES(1, 1, 1);
                INSERT INTO itemData VALUES(1, 2, 2);
                INSERT INTO itemData VALUES(1, 3, 3);
                INSERT INTO itemData VALUES(1, 4, 4);
                INSERT INTO creators VALUES(1, 'Ada', 'Lovelace');
                INSERT INTO itemCreators VALUES(1, 1, 0);
                INSERT INTO itemNotes VALUES(3, 1, '<p>noteneedle personal note</p>', 'Reading note');
                INSERT INTO itemAttachments VALUES(2, 1, 'storage:paper.pdf', 'application/pdf', 'Cached PDF');
                INSERT INTO itemAnnotations VALUES(4, 2, 'annotationneedle selected text', 'comment text', '7', '#ffd400');
                INSERT INTO itemAttachments VALUES(5, 1, 'storage:supp.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Supplement');
                INSERT INTO itemAttachments VALUES(6, 1, 'storage:missing.pdf', 'application/pdf', 'Missing');
                """
            )
            zconn.commit()
            zconn.close()

            index_db = sqlite3.connect(temp_dir / "index.sqlite")
            index_db.row_factory = sqlite3.Row
            ensure_schema(index_db)
            summary = index_zotero(index_db, {"zotero_sqlite": str(zotero_path), "index": {"zotero_chunk_chars": 500}})

            self.assertEqual(summary["docs"], 1)
            self.assertEqual(summary["notes"], 1)
            self.assertEqual(summary["annotations"], 1)
            self.assertEqual(summary["fulltext"], 1)
            self.assertEqual(summary["attachments"], 1)
            self.assertEqual(len(summary["warnings"]), 1)

            for term in ["noteneedle", "annotationneedle", "fulltextneedle", "attachmentneedle"]:
                row = index_db.execute(
                    "SELECT COUNT(*) AS count FROM zotero_evidence_fts WHERE zotero_evidence_fts MATCH ?",
                    (term,),
                ).fetchone()
                self.assertEqual(row["count"], 1, term)
            index_db.commit()
            index_db.close()

            payload = search_local(
                {"index": {"db_path": str(temp_dir / "index.sqlite")}},
                SearchRequest(query="attachmentneedle", target="zotero", profile="fast", limit=3),
            )
            self.assertEqual(payload["hits"][0]["source"], "zotero")
            self.assertEqual(payload["hits"][0]["route"], "zotero_attachments")


class FolderSourceTests(unittest.TestCase):
    def test_multiple_folder_libraries_are_indexed_and_searchable(self) -> None:
        with scratch_dir("folder_source") as temp_dir:
            folder_a = temp_dir / "folder-a"
            folder_b = temp_dir / "folder-b"
            excluded = folder_a / "skip"
            excluded.mkdir(parents=True)
            folder_b.mkdir(parents=True)
            (folder_a / "notes.md").write_text("# Alpha\n\nfolderneedle markdown evidence", encoding="utf-8")
            (folder_a / "plain.txt").write_text("txtneedle plain text evidence", encoding="utf-8")
            _write_docx(folder_b / "doc.docx", "docxneedle folder evidence")
            _write_pptx(folder_b / "slides.pptx", "pptxneedle folder evidence")
            _write_xlsx(folder_b / "sheet.xlsx", "xlsxneedle folder evidence")
            (folder_b / "paper.pdf").write_bytes(b"%PDF-test")
            (folder_b / "ignore.bin").write_text("ignoredneedle", encoding="utf-8")
            (excluded / "hidden.md").write_text("excludedneedle", encoding="utf-8")

            config = {
                "folder_libraries": [
                    {"id": "alpha", "name": "Alpha Folder", "path": str(folder_a), "enabled": True},
                    {"id": "beta", "name": "Beta Folder", "path": str(folder_b), "enabled": True},
                ],
                "exclude_dirs": ["skip"],
                "index": {"folder_chunk_chars": 500, "db_path": str(temp_dir / "index.sqlite")},
                "folder": {
                    "include_extensions": [".md", ".txt", ".docx", ".pptx", ".xlsx", ".pdf"],
                },
            }
            index_db = sqlite3.connect(temp_dir / "index.sqlite")
            index_db.row_factory = sqlite3.Row
            ensure_schema(index_db)
            with patch("local_knowledge_bridge.folder.extract_pdf_pages", return_value=["pdfneedle folder evidence"]):
                summary = index_folder(index_db, config)

            self.assertEqual(summary["warnings"], [])
            self.assertEqual(summary["docs"], 6)
            self.assertGreaterEqual(summary["chunks"], 6)
            row = index_db.execute(
                "SELECT COUNT(*) AS count FROM folder_chunk_fts WHERE folder_chunk_fts MATCH ?",
                ("excludedneedle",),
            ).fetchone()
            self.assertEqual(row["count"], 0)
            index_db.commit()
            index_db.close()

            payload = search_local(
                config,
                SearchRequest(query="docxneedle", target="folder", profile="fast", limit=3),
            )
            self.assertEqual(payload["hits"][0]["source"], "folder")
            self.assertEqual(payload["hits"][0]["library_id"], "beta")
            self.assertEqual(payload["hits"][0]["library_name"], "Beta Folder")


if __name__ == "__main__":
    unittest.main()

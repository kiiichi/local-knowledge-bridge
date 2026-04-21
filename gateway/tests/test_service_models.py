from __future__ import annotations

import sys
import unittest
from pathlib import Path

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge.service_models import AskRequest, ReportRequest, SearchHit, SearchRequest


class RequestModelTests(unittest.TestCase):
    def test_search_request_defaults_to_hybrid_mode(self) -> None:
        request = SearchRequest(query="passive linear optics")
        self.assertEqual(request.mode, "hybrid")

    def test_search_request_normalizes_explicit_mode(self) -> None:
        request = SearchRequest(query="passive linear optics", mode="LEXICAL")
        self.assertEqual(request.mode, "lexical")

    def test_search_request_rejects_invalid_mode(self) -> None:
        with self.assertRaises(SystemExit):
            SearchRequest(query="passive linear optics", mode="vector")

    def test_ask_request_from_mapping_preserves_question_and_mode(self) -> None:
        request = AskRequest.from_mapping({"question": "What is passive linear optics?", "mode": "semantic"})
        self.assertEqual(request.question, "What is passive linear optics?")
        self.assertEqual(request.query, "What is passive linear optics?")
        self.assertEqual(request.mode, "semantic")

    def test_report_request_from_mapping_preserves_read_top_and_mode(self) -> None:
        request = ReportRequest.from_mapping({"query": "passive linear optics", "mode": "lexical", "read_top": 5})
        self.assertEqual(request.query, "passive linear optics")
        self.assertEqual(request.mode, "lexical")
        self.assertEqual(request.read_top, 5)

    def test_search_hit_to_dict_exposes_stable_deep_scores_without_internal_text(self) -> None:
        hit = SearchHit(
            source="obsidian",
            route="obsidian_notes",
            title="Passive Linear Optics",
            path="notes/passive-linear-optics.md",
            locator="",
            snippet="passive linear optics",
            year="2024",
            doi="10.1000/example",
            canonical_key="doi:10.1000/example",
            full_path="C:\\notes\\passive-linear-optics.md",
            semantic_score=0.77,
            rerank_score=0.33,
            semantic_text="hidden body",
            extra={"bm25_score": 1.2},
        )

        payload = hit.to_dict()

        self.assertEqual(payload["semantic_score"], 0.77)
        self.assertEqual(payload["rerank_score"], 0.33)
        self.assertNotIn("semantic_text", payload)
        self.assertEqual(payload["extra"]["bm25_score"], 1.2)


if __name__ == "__main__":
    unittest.main()

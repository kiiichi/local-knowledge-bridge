from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(__file__).resolve().parent
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from local_knowledge_bridge import evals, reporting, retrieval
from local_knowledge_bridge.scoring import QueryContext
from local_knowledge_bridge.service_models import SearchHit, SearchRequest
from support import scratch_dir


class DummyConnection:
    def close(self) -> None:
        return


class RetrievalModeContractTests(unittest.TestCase):
    def test_search_local_returns_mode_and_effective_mode(self) -> None:
        request = SearchRequest(query="passive linear optics", target="obsidian", profile="balanced", mode="semantic", limit=3)
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
            hybrid_score=55.0,
        )

        with (
            patch.object(retrieval, "selected_profile", return_value="balanced"),
            patch.object(retrieval, "ensure_index_ready"),
            patch.object(retrieval, "connect_index", return_value=DummyConnection()),
            patch.object(retrieval, "ensure_schema"),
            patch.object(retrieval, "profile_settings", return_value={"top_k_recall": 12}),
            patch.object(retrieval, "route_weights", return_value={"obsidian_notes": 1.2}),
            patch.object(retrieval, "scoring_settings", return_value={"char_ngram_n": 3}),
            patch.object(
                retrieval,
                "build_query_context",
                return_value=QueryContext(
                    query=request.query,
                    base_tokens=["passive", "linear", "optics"],
                    expanded_tokens=["passive", "linear", "optics"],
                    query_ngrams={},
                    fts_query='"passive linear optics"',
                ),
            ),
            patch.object(retrieval, "parse_year_filters", return_value=[]),
            patch.object(retrieval, "_index_db_path", return_value=Path("C:/gateway/.tmp/tests/index/lkb_index.sqlite")),
            patch.object(retrieval, "_query_route", side_effect=[[hit], []]) as query_route,
            patch.object(retrieval, "fuse_hits", return_value=[hit]),
        ):
            payload = retrieval.search_local({}, request)

        self.assertEqual(payload["mode"], "semantic")
        self.assertEqual(payload["debug"]["effective_mode"], "semantic")
        self.assertEqual(payload["hits"][0]["title"], "Passive Linear Optics")
        self.assertEqual(payload["hits"][0]["hybrid_score"], 55.0)
        self.assertTrue(all(call.kwargs["mode"] == "semantic" for call in query_route.call_args_list))

    def test_report_payload_includes_mode_headers(self) -> None:
        payload = {
            "target": "both",
            "profile": "balanced",
            "mode": "semantic",
            "hits": [
                {
                    "source": "obsidian",
                    "route": "obsidian_notes",
                    "title": "Passive Linear Optics",
                    "path": "notes/passive-linear-optics.md",
                    "locator": "",
                    "snippet": "passive linear optics",
                    "year": "2024",
                    "doi": "10.1000/example",
                    "canonical_key": "doi:10.1000/example",
                    "full_path": "C:\\notes\\passive-linear-optics.md",
                    "score": 0.5,
                    "lexical_score": 33.0,
                    "hybrid_score": 44.0,
                    "semantic_score": 0.77,
                    "rerank_score": 0.22,
                    "library_id": "",
                    "library_name": "",
                    "routes": ["obsidian_notes"],
                    "extra": {},
                }
            ],
            "total_hits": 1,
            "debug": {"effective_mode": "lexical"},
        }

        result = reporting.build_report_payload("passive linear optics", payload, 3)

        self.assertIn("MODE: semantic", result["report_markdown"])
        self.assertIn("EFFECTIVE_MODE: lexical", result["report_markdown"])
        self.assertIn("hybrid_score=44.000000", result["report_markdown"])
        self.assertIn("semantic_score=0.770000", result["report_markdown"])
        self.assertIn("rerank_score=0.220000", result["report_markdown"])

    def test_search_local_routes_deep_profile_into_deep_ranking(self) -> None:
        request = SearchRequest(query="passive linear optics", target="obsidian", profile="deep", mode="hybrid", limit=3)
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
            hybrid_score=55.0,
            semantic_text="body",
        )

        with (
            patch.object(retrieval, "selected_profile", return_value="deep"),
            patch.object(retrieval, "ensure_index_ready"),
            patch.object(retrieval, "connect_index", return_value=DummyConnection()),
            patch.object(retrieval, "ensure_schema"),
            patch.object(retrieval, "profile_settings", return_value={"top_k_recall": 12}),
            patch.object(retrieval, "route_weights", return_value={"obsidian_notes": 1.2}),
            patch.object(retrieval, "scoring_settings", return_value={"char_ngram_n": 3}),
            patch.object(
                retrieval,
                "build_query_context",
                return_value=QueryContext(
                    query=request.query,
                    base_tokens=["passive", "linear", "optics"],
                    expanded_tokens=["passive", "linear", "optics"],
                    query_ngrams={},
                    fts_query='"passive linear optics"',
                ),
            ),
            patch.object(retrieval, "parse_year_filters", return_value=[]),
            patch.object(retrieval, "_index_db_path", return_value=Path("C:/gateway/.tmp/tests/index/lkb_index.sqlite")),
            patch.object(retrieval, "_query_route", side_effect=[[hit], []]),
            patch.object(retrieval, "fuse_hits", return_value=[hit]),
            patch.object(retrieval, "apply_deep_ranking", return_value=[hit]) as apply_deep_ranking,
        ):
            payload = retrieval.search_local({}, request)

        self.assertEqual(payload["profile"], "deep")
        apply_deep_ranking.assert_called_once_with(request.query, [hit], {}, top_k_rerank=20)

    def test_search_local_both_queries_all_source_routes(self) -> None:
        request = SearchRequest(query="passive linear optics", target="both", profile="balanced", mode="hybrid", limit=3)

        with (
            patch.object(retrieval, "selected_profile", return_value="balanced"),
            patch.object(retrieval, "ensure_index_ready"),
            patch.object(retrieval, "connect_index", return_value=DummyConnection()),
            patch.object(retrieval, "ensure_schema"),
            patch.object(retrieval, "profile_settings", return_value={"top_k_recall": 12}),
            patch.object(
                retrieval,
                "route_weights",
                return_value={
                    "obsidian_notes": 1.2,
                    "obsidian_chunks": 1.4,
                    "endnote_docs": 1.1,
                    "endnote_attachments": 0.95,
                    "endnote_fulltext": 1.0,
                    "zotero_docs": 1.1,
                    "zotero_notes": 1.2,
                    "zotero_annotations": 1.25,
                    "zotero_fulltext": 1.0,
                    "zotero_attachments": 0.95,
                    "folder_docs": 0.85,
                    "folder_chunks": 1.0,
                },
            ),
            patch.object(retrieval, "scoring_settings", return_value={"char_ngram_n": 3}),
            patch.object(
                retrieval,
                "build_query_context",
                return_value=QueryContext(
                    query=request.query,
                    base_tokens=["passive", "linear", "optics"],
                    expanded_tokens=["passive", "linear", "optics"],
                    query_ngrams={},
                    fts_query='"passive linear optics"',
                ),
            ),
            patch.object(retrieval, "parse_year_filters", return_value=[]),
            patch.object(retrieval, "_index_db_path", return_value=Path("C:/gateway/.tmp/tests/index/lkb_index.sqlite")),
            patch.object(retrieval, "_query_route", return_value=[]) as query_route,
            patch.object(retrieval, "fuse_hits", return_value=[]),
        ):
            payload = retrieval.search_local({}, request)

        self.assertEqual(payload["target"], "both")
        self.assertEqual(
            [call.kwargs["route"] for call in query_route.call_args_list],
            [
                "obsidian_notes",
                "obsidian_chunks",
                "endnote_docs",
                "endnote_attachments",
                "endnote_fulltext",
                "zotero_docs",
                "zotero_notes",
                "zotero_annotations",
                "zotero_fulltext",
                "zotero_attachments",
                "folder_docs",
                "folder_chunks",
            ],
        )


class EvalModeTests(unittest.TestCase):
    def test_evaluate_cases_baseline_uses_lexical_mode(self) -> None:
        captured_requests: list[SearchRequest] = []

        with scratch_dir("eval_mode_tests") as temp_dir:
            cases_path = temp_dir / "cases.jsonl"
            cases_path.write_text(json.dumps({"query": "passive linear optics", "target": "both", "must_have": []}) + "\n", encoding="utf-8")

            def fake_search_local(config: dict, request: SearchRequest) -> dict:
                captured_requests.append(request)
                return {"hits": []}

            with (
                patch.object(evals, "eval_cases_path", return_value=cases_path),
                patch.object(evals, "search_local", side_effect=fake_search_local),
            ):
                metrics = evals.evaluate_cases({}, baseline=True)

        self.assertEqual(metrics["profile"], "baseline")
        self.assertEqual(len(captured_requests), 1)
        self.assertEqual(captured_requests[0].profile, "fast")
        self.assertEqual(captured_requests[0].mode, "lexical")


if __name__ == "__main__":
    unittest.main()

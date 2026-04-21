from __future__ import annotations

import sys
import unittest
from pathlib import Path

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge.config import route_weights, scoring_settings
from local_knowledge_bridge.ranking import fuse_hits
from local_knowledge_bridge.scoring import build_fts_query, build_query_context, expand_query_tokens, score_document, tokenize
from local_knowledge_bridge.service_models import SearchHit


class ScoringTests(unittest.TestCase):
    def test_tokenize_keeps_cjk_run_and_bigrams(self) -> None:
        self.assertEqual(tokenize("量子态 tomography"), ["量子态", "量子", "子态", "tomography"])

    def test_expand_query_tokens_adds_legacy_synonyms(self) -> None:
        base, expanded = expand_query_tokens("surface water mapping sentinel-2")
        self.assertEqual(base, ["surface", "water", "mapping", "sentinel-2"])
        self.assertIn("msi", expanded)
        self.assertIn("inland water", expanded)
        self.assertIn("classification", expanded)

    def test_build_fts_query_uses_phrase_and_expanded_tokens(self) -> None:
        query = build_fts_query("passive linear optics", ["passive", "linear", "optics"])
        self.assertEqual(query, '"passive linear optics" OR "passive" OR "linear" OR "optics"')

    def test_hybrid_scoring_beats_lexical_for_paraphrase(self) -> None:
        context = build_query_context("surface water mapping sentinel-2")
        scores = score_document(
            mode="hybrid",
            title="MSI delineation of lakes",
            body="Sentinel2 extraction of alpine lake inventory from imagery",
            bm25_score=1.5,
            query_context=context,
        )
        self.assertGreater(scores["hybrid_score"], scores["lexical_score"])
        self.assertGreater(scores["semantic_score"], 0.0)


class ConfigTests(unittest.TestCase):
    def test_route_weights_support_partial_override(self) -> None:
        weights = route_weights({"retrieval": {"route_weights": {"obsidian_notes": 2.5}}})
        self.assertEqual(weights["obsidian_notes"], 2.5)
        self.assertEqual(weights["endnote_docs"], 1.1)

    def test_scoring_settings_support_partial_override(self) -> None:
        settings = scoring_settings({"retrieval": {"scoring": {"char_ngram_weight": 33, "title_hit_cap": 5}}})
        self.assertEqual(settings["char_ngram_weight"], 33.0)
        self.assertEqual(settings["title_hit_cap"], 5)
        self.assertEqual(settings["text_hit_cap"], 12)


class RankingTests(unittest.TestCase):
    def test_fuse_hits_uses_configured_route_weights(self) -> None:
        note_hit = SearchHit(
            source="obsidian",
            route="obsidian_notes",
            title="Note A",
            path="note-a.md",
            locator="",
            snippet="snippet",
            year="2024",
            doi="",
            canonical_key="same-key",
            full_path="C:\\notes\\note-a.md",
            lexical_score=10.0,
            hybrid_score=20.0,
        )
        chunk_hit = SearchHit(
            source="obsidian",
            route="obsidian_chunks",
            title="Note A",
            path="note-a.md",
            locator="Section",
            snippet="snippet",
            year="2024",
            doi="",
            canonical_key="same-key",
            full_path="C:\\notes\\note-a.md",
            lexical_score=12.0,
            hybrid_score=25.0,
        )

        fused = fuse_hits(
            {"obsidian_notes": [note_hit], "obsidian_chunks": [chunk_hit]},
            route_weights={"obsidian_notes": 0.5, "obsidian_chunks": 2.0},
        )

        self.assertEqual(len(fused), 1)
        self.assertAlmostEqual(fused[0].score, (0.5 / 61.0) + (2.0 / 61.0), places=6)
        self.assertEqual(fused[0].hybrid_score, 25.0)


if __name__ == "__main__":
    unittest.main()

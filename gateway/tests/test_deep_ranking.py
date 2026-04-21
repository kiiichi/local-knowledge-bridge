from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = GATEWAY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from local_knowledge_bridge import deep_ranking
from local_knowledge_bridge.service_models import SearchHit


class FakeEmbeddingModel:
    def encode(self, texts, **kwargs):
        if len(texts) == 1:
            return [[1.0, 0.0]]
        return [[0.9, 0.1], [0.1, 0.9]]


class FakeReranker:
    def predict(self, pairs, **kwargs):
        return [0.2, 0.8]


class DeepRankingTests(unittest.TestCase):
    def _hits(self) -> list[SearchHit]:
        return [
            SearchHit(
                source="obsidian",
                route="obsidian_notes",
                title="Passive Linear Optics",
                path="note-a.md",
                locator="Intro",
                snippet="passive linear optics",
                year="2024",
                doi="10.1000/example-a",
                canonical_key="doi:10.1000/example-a",
                full_path="C:\\notes\\note-a.md",
                score=0.6,
                lexical_score=10.0,
                hybrid_score=20.0,
                semantic_text="first body",
                routes=["obsidian_notes"],
            ),
            SearchHit(
                source="endnote",
                route="endnote_fulltext",
                title="Optical Networks",
                path="paper-b.pdf",
                locator="p.3",
                snippet="optical network paper",
                year="2023",
                doi="10.1000/example-b",
                canonical_key="doi:10.1000/example-b",
                full_path="C:\\papers\\paper-b.pdf",
                score=0.5,
                lexical_score=9.0,
                hybrid_score=18.0,
                semantic_text="second body",
                routes=["endnote_fulltext"],
            ),
        ]

    def test_model_text_for_hit_uses_title_locator_snippet_and_body(self) -> None:
        text = deep_ranking.model_text_for_hit(self._hits()[0], limit=500)
        self.assertIn("Passive Linear Optics", text)
        self.assertIn("Intro", text)
        self.assertIn("passive linear optics", text)
        self.assertIn("first body", text)

    def test_apply_deep_ranking_populates_semantic_and_rerank_scores(self) -> None:
        hits = self._hits()
        with (
            patch.object(deep_ranking, "load_embedding_model", return_value=FakeEmbeddingModel()),
            patch.object(deep_ranking, "load_reranker_model", return_value=FakeReranker()),
        ):
            ranked = deep_ranking.apply_deep_ranking("passive linear optics", hits, {}, top_k_rerank=2)

        self.assertEqual(len(ranked), 2)
        self.assertTrue(all(hit.semantic_score > 0.0 for hit in ranked))
        self.assertTrue(any(hit.rerank_score > 0.0 for hit in ranked))
        self.assertEqual(ranked[0].title, "Optical Networks")


if __name__ == "__main__":
    unittest.main()

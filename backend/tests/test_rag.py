"""Retrieval-layer tests. Nothing here loads an embedding model."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest

from app.ingest import preprocessor
from app.rag import chunker, compressor, retriever
from app.rag.bm25_index import BM25Index, tokenize
from app.rag.retriever import reciprocal_rank_fusion
from app.tools.patterns import detect_hazard_type
from app.tools.retrieval import clause_family


class TestReciprocalRankFusion:
    def test_agreement_between_retrievers_wins(self) -> None:
        dense = ["a", "b", "c"]
        sparse = ["c", "a", "d"]
        # a: 1/60 + 1/61, c: 1/62 + 1/60 -- a is ranked higher by both lists.
        assert reciprocal_rank_fusion([dense, sparse])[0] == "a"

    def test_every_document_from_every_list_survives(self) -> None:
        merged = reciprocal_rank_fusion([["a", "b"], ["c"], []])
        assert sorted(merged) == ["a", "b", "c"]

    def test_scores_are_monotonic_in_rank(self) -> None:
        assert reciprocal_rank_fusion([["a", "b", "c"]]) == ["a", "b", "c"]

    def test_empty_input_is_empty_output(self) -> None:
        assert reciprocal_rank_fusion([]) == []

    def test_larger_k_flattens_the_ranking_advantage(self) -> None:
        lists = [["a", "b"], ["b", "a"]]
        # With both documents in both lists the order is stable; k only scales the gap.
        assert set(reciprocal_rank_fusion(lists, k=1)) == set(reciprocal_rank_fusion(lists, k=600))


class TestBM25Index:
    def test_finds_the_document_containing_the_query_terms(self) -> None:
        index = BM25Index.build(
            ["c1", "c2", "c3"],
            [
                "lockout tagout procedure for the hydraulic press",
                "fall protection anchorage on the roof edge",
                "forklift pedestrian traffic in the warehouse aisle",
            ],
        )
        assert index.search("hydraulic press lockout", 1)[0][0] == "c1"

    def test_no_match_returns_nothing_rather_than_noise(self) -> None:
        index = BM25Index.build(["c1"], ["lockout tagout procedure"])
        assert index.search("xyzzy", 5) == []

    def test_empty_index_is_safe_to_query(self) -> None:
        assert BM25Index.build([], []).search("anything", 5) == []

    def test_round_trips_through_disk(self, tmp_path) -> None:
        index = BM25Index.build(["c1", "c2"], ["confined space entry permit", "hot work fire watch"])
        path = tmp_path / "bm25.pkl"
        index.save(path)
        reloaded = BM25Index.load(path)
        assert reloaded is not None
        assert reloaded.search("confined space", 1)[0][0] == "c1"

    def test_missing_file_loads_as_none(self, tmp_path) -> None:
        assert BM25Index.load(tmp_path / "absent.pkl") is None

    def test_tokenizer_drops_punctuation_and_case(self) -> None:
        assert tokenize("LOTO: 29 CFR 1910.147(c)(4)!") == ["loto", "29", "cfr", "1910", "147", "c", "4"]


class TestChunker:
    def test_sentences_split_on_terminators_only(self) -> None:
        text = "The press cycled. It struck the operator. No guard was fitted."
        assert len(chunker.split_sentences(text)) == 3

    def test_abbreviated_citation_is_not_a_sentence_break(self) -> None:
        # A split requires a capital letter after the space, so "29 CFR 1910.147" stays whole.
        assert len(chunker.split_sentences("Cited under 29 CFR 1910.147 for the violation.")) == 1

    def test_headings_start_new_sections(self) -> None:
        text = "INTRODUCTION\nSomething happened here.\nFINDINGS\nSomething else was found."
        sections = chunker.split_sections(text)
        assert [heading for heading, _ in sections] == ["INTRODUCTION", "FINDINGS"]

    def test_body_before_the_first_heading_is_kept(self) -> None:
        sections = chunker.split_sections("Preamble text.\nFINDINGS\nThe finding.")
        assert sections[0] == ("", "Preamble text.")


class TestPreprocessor:
    def test_running_headers_are_removed(self) -> None:
        pages = [f"OSHA Investigation Report\nPage body {n}\nFooter line" for n in range(4)]
        cleaned = preprocessor.clean_pages(pages)
        assert "OSHA Investigation Report" not in cleaned
        assert "Page body 2" in cleaned

    def test_short_documents_keep_every_line(self) -> None:
        cleaned = preprocessor.clean_pages(["Title\nBody", "Title\nMore"])
        assert cleaned.count("Title") == 2

    def test_hyphenated_line_wrap_is_rejoined(self) -> None:
        assert "lockout" in preprocessor.normalize("The lock-\nout procedure")

    def test_soft_wraps_become_spaces_but_paragraphs_survive(self) -> None:
        cleaned = preprocessor.normalize("first line\nsecond line.\n\nNew paragraph.")
        assert "first line second line." in cleaned
        assert "\n\n" in cleaned


class TestClauseFamilyRegexes:
    def test_machine_guarding_range_does_not_swallow_hazcom(self) -> None:
        assert clause_family("29 CFR 1910.1200") == "hazcom"
        assert clause_family("29 CFR 1910.212") == "machine_guarding"


class TestReranker:
    """The adapter around FlashRank -- where our bugs would be, not theirs."""

    @staticmethod
    def _candidates() -> list[dict]:
        return [
            {"chunk_id": "a", "text": "fall protection anchorage", "score": 0.1},
            {"chunk_id": "b", "text": "lockout verification step", "score": 0.2},
            {"chunk_id": "c", "text": "forklift traffic", "score": 0.3},
        ]

    def test_reordering_and_scores_follow_the_ranker(self, monkeypatch) -> None:
        class Ranker:
            def rerank(self, request):
                # FlashRank returns descending score with the caller's own ids.
                return [{"id": 1, "score": 0.96}, {"id": 0, "score": 0.10}, {"id": 2, "score": 0.0}]

        monkeypatch.setattr(retriever, "_reranker", lambda: Ranker())
        monkeypatch.setitem(sys.modules, "flashrank", types.SimpleNamespace(RerankRequest=dict))

        result = retriever._rerank("lockout", self._candidates(), top_k=2)
        assert [item["chunk_id"] for item in result] == ["b", "a"]
        assert result[0]["score"] == pytest.approx(0.96)

    def test_unavailable_reranker_keeps_the_fusion_order(self, monkeypatch) -> None:
        monkeypatch.setattr(retriever, "_reranker", lambda: None)
        result = retriever._rerank("lockout", self._candidates(), top_k=2)
        assert [item["chunk_id"] for item in result] == ["a", "b"]

    def test_empty_candidate_set_is_handled(self, monkeypatch) -> None:
        monkeypatch.setattr(retriever, "_reranker", lambda: object())
        assert retriever._rerank("lockout", [], top_k=5) == []


class TestCompressor:
    @staticmethod
    def _install(monkeypatch, scores: list[float]) -> list[int]:
        """Replace the embedder with a scripted one; return a per-call counter."""
        calls: list[int] = []

        def embed_documents(texts):
            calls.append(len(texts))
            return np.array(scores[: len(texts)], dtype=np.float32).reshape(-1, 1)

        monkeypatch.setattr(compressor, "embed_documents", embed_documents)
        monkeypatch.setattr(compressor, "embed_query", lambda _query: np.array([1.0], dtype=np.float32))
        return calls

    def test_whole_result_set_costs_one_embedding_pass(self, monkeypatch) -> None:
        calls = self._install(monkeypatch, [0.9, 0.1, 0.9, 0.1])
        texts = ["Relevant one. Irrelevant one.", "Relevant two. Irrelevant two."]
        compressor.compress_all("query", texts)
        assert calls == [4], "expected a single batched call covering every sentence"

    def test_irrelevant_sentences_are_dropped(self, monkeypatch) -> None:
        self._install(monkeypatch, [0.9, 0.1])
        result = compressor.compress_all("query", ["Keep this one. Drop this one."])
        assert result == ["Keep this one."]

    def test_single_sentence_text_is_not_embedded_at_all(self, monkeypatch) -> None:
        calls = self._install(monkeypatch, [])
        assert compressor.compress_all("query", ["Only one sentence."]) == ["Only one sentence."]
        assert calls == []

    def test_nothing_above_threshold_keeps_the_best_sentence(self, monkeypatch) -> None:
        self._install(monkeypatch, [0.05, 0.2])
        result = compressor.compress_all("query", ["Weak match. Stronger match."])
        assert result == ["Stronger match."]

    def test_empty_input_is_empty_output(self) -> None:
        assert compressor.compress_all("query", []) == []


class TestIndexPathsAgree:
    """The ingest writer and the retriever reader must resolve to one directory."""

    def test_bm25_index_is_written_where_the_retriever_looks(self, tmp_path, monkeypatch) -> None:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        import _ingest_common

        from app.config import settings
        from app.rag import local_store, vector_store

        monkeypatch.setattr(settings, "data_dir", tmp_path)
        monkeypatch.setattr(vector_store, "ensure_collection", lambda _name: None)
        monkeypatch.setattr(
            _ingest_common, "embed_documents", lambda texts: np.ones((len(texts), 384), dtype=np.float32)
        )
        _ingest_common.index_chunks("c", ["id1"], [{"text": "lockout tagout procedure"}])

        # Exactly the path app/rag/retriever.py::_bm25_for reads.
        assert (settings.data_dir / "bm25_c.pkl").exists()
        assert BM25Index.load(settings.data_dir / "bm25_c.pkl") is not None
        assert local_store.vectors_path("c").exists()


class TestCorpusMetadataUsesWholeDocument:
    """Investigation reports open with front matter that describes no incident."""

    COVER = (
        "Chemical Reaction and Toxic Gas Release at Bio-Lab, Inc. "
        "U.S. Chemical Safety and Hazard Investigation Board. Published April 2023. "
        "Table of Contents. List of Figures. Legal Notice. Abbreviations.\n"
    )
    BODY = (
        "The refinery process unit experienced a runaway reaction. A relief valve was "
        "isolated and the reactor over-pressured, releasing toxic gas across the "
        "petrochemical plant. Operators had normalised repeated nuisance alarms."
    )

    def test_the_front_matter_alone_classifies_nothing(self) -> None:
        from _ingest_common import detect_industry

        assert detect_industry(self.COVER) == "unknown"
        assert detect_hazard_type(self.COVER) == "general"

    def test_the_full_document_classifies_correctly(self) -> None:
        from _ingest_common import detect_industry

        document = self.COVER + self.BODY
        assert detect_industry(document) == "chemical"
        assert detect_hazard_type(document) == "chemical_release"

    def test_ingest_classifies_from_the_full_text(self, tmp_path) -> None:
        import ingest_corpus

        document = self.COVER * 40 + self.BODY  # front matter far exceeds any window
        metadata = ingest_corpus.document_metadata(tmp_path / "report.pdf", document)
        assert metadata["industry"] == "chemical"
        assert metadata["hazard_type"] == "chemical_release"


class TestIndustryDetection:
    """Industry is shown in the UI and drives the retrieval filter."""

    def test_whole_words_only(self) -> None:
        from _ingest_common import detect_industry

        # "mine" hides in "determined"/"examined"; "press" in "pressure".
        assert detect_industry("we determined the cause and examined the pressure vessel") == "unknown"
        assert detect_industry("pressure relief valve pressure pressure pressure") == "unknown"

    def test_a_dominant_vocabulary_wins(self) -> None:
        from _ingest_common import detect_industry

        assert detect_industry("chemical " * 20 + "reactor catalyst feedstock refinery") == "chemical"

    def test_a_passing_mention_does_not_decide_the_label(self) -> None:
        from _ingest_common import detect_industry

        # One contractor in a report that is otherwise about nothing in particular.
        assert detect_industry("a general contractor attended the site once") == "unknown"

    def test_a_mixed_document_stays_unknown(self) -> None:
        from _ingest_common import MIN_INDUSTRY_HITS, detect_industry

        mixed = ("chemical " * MIN_INDUSTRY_HITS) + ("warehouse " * MIN_INDUSTRY_HITS)
        assert detect_industry(mixed) == "unknown", "no clear margin means no guess"

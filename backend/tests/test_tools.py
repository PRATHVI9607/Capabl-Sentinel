"""Tool-level tests: the deterministic logic the risk number depends on."""

from __future__ import annotations

import pytest

from app import llm
from app.models import RegulatoryClause, RetrievedChunk, SeverityTier, SimilarIncident, Urgency
from app.tools import actions, parsing, patterns, retrieval, scoring
from tests.fixtures import FakeLLM


def make_similar(excerpt: str) -> SimilarIncident:
    return SimilarIncident(
        doc_id="d1",
        title="t",
        similarity_score=0.5,
        chunk_excerpt=excerpt,
        source_document="d1.pdf",
    )


class TestComputeRiskScore:
    def test_matches_the_documented_formula(self) -> None:
        score = scoring.compute_risk_score(
            severity=SeverityTier.CRITICAL,
            similar_count=4,
            corpus_size=80,
            violated_clauses=["lockout_tagout"],
            detected_precursors=2,
            known_precursors=10,
        )
        # frequency = 4/80 * 25 = 1.25; regulatory = 1.8 * 1.2 = 2.16; precursor = 2.0
        # 0.30*9.5 + 0.25*1.25 + 0.25*2.16 + 0.20*2.0 = 2.85 + 0.3125 + 0.54 + 0.40
        assert score.total == pytest.approx(4.10)
        assert score.tier is SeverityTier.MEDIUM
        assert [c.name for c in score.components] == [
            "Severity",
            "Frequency",
            "Regulatory",
            "Precursor Density",
        ]
        assert sum(c.weight for c in score.components) == pytest.approx(1.0)

    def test_every_component_is_capped_at_ten(self) -> None:
        score = scoring.compute_risk_score(
            severity=SeverityTier.CRITICAL,
            similar_count=50,
            corpus_size=50,
            violated_clauses=["general_duty_clause"] * 20,
            detected_precursors=99,
            known_precursors=1,
        )
        assert all(component.score <= 10.0 for component in score.components)
        assert score.total <= 10.0
        assert score.tier is SeverityTier.CRITICAL

    def test_empty_corpus_does_not_divide_by_zero(self) -> None:
        score = scoring.compute_risk_score(
            severity=SeverityTier.UNKNOWN,
            similar_count=0,
            corpus_size=0,
            violated_clauses=[],
            detected_precursors=0,
            known_precursors=0,
        )
        assert score.total == pytest.approx(1.2)
        assert score.tier is SeverityTier.LOW

    @pytest.mark.parametrize(
        ("total", "expected"),
        [
            (9.9, SeverityTier.CRITICAL),
            (8.0, SeverityTier.CRITICAL),
            (7.99, SeverityTier.HIGH),
            (6.0, SeverityTier.HIGH),
            (4.0, SeverityTier.MEDIUM),
            (3.99, SeverityTier.LOW),
        ],
    )
    def test_tier_boundaries(self, total: float, expected: SeverityTier) -> None:
        assert scoring.tier_for(total) is expected


class TestClassifySeverity:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("The employee was pronounced dead at the scene.", SeverityTier.CRITICAL),
            ("The worker suffered an amputation of two fingers.", SeverityTier.HIGH),
            ("The operator received a laceration requiring stitches.", SeverityTier.MEDIUM),
            ("A near miss was reported; nobody was hurt.", SeverityTier.LOW),
        ],
    )
    def test_keyword_rules(self, text: str, expected: SeverityTier) -> None:
        assert scoring.classify_severity_by_rules(text) is expected

    def test_counts_outrank_absent_keywords(self) -> None:
        assert (
            scoring.classify_severity_by_rules("An event occurred.", fatality_count=1)
            is SeverityTier.CRITICAL
        )
        assert scoring.classify_severity_by_rules("An event occurred.", injury_count=4) is SeverityTier.HIGH

    def test_undecidable_text_returns_none(self) -> None:
        assert scoring.classify_severity_by_rules("Routine equipment inspection log.") is None


class TestPrecursorDetection:
    def test_requires_corroboration_across_history(self) -> None:
        text = "The technician did not verify the isolation and the machine still running started."
        history = [make_similar("crew did not verify zero energy") for _ in range(3)]
        found = patterns.detect_precursor_patterns(text, history, hazard_type="lockout_tagout")
        assert "Verification step omitted" in {p.pattern_name for p in found}

    def test_uncorroborated_pattern_is_reported_with_zero_evidence(self) -> None:
        # Only ~8 compressed excerpts are retrieved, so any corroboration cutoff
        # hides real findings. The count is the signal, and 0 is a valid value.
        text = "The technician did not verify the isolation."
        history = [make_similar("unrelated forklift incident")]
        found = patterns.detect_precursor_patterns(text, history, hazard_type="lockout_tagout")
        assert [p.pattern_name for p in found] == ["Verification step omitted"]
        assert found[0].evidence_count == 0

    def test_patterns_are_ranked_by_corroboration(self) -> None:
        text = "The crew did not verify isolation and the machine still running was cleared."
        history = [make_similar("did not verify zero energy") for _ in range(3)]
        found = patterns.detect_precursor_patterns(text, history, hazard_type="lockout_tagout")
        counts = [p.evidence_count for p in found]
        assert counts == sorted(counts, reverse=True)
        assert counts[0] == 3

    def test_confidence_rises_with_evidence_and_is_capped(self) -> None:
        text = "The technician did not verify the isolation."
        alone = patterns.detect_precursor_patterns(text, [], hazard_type="lockout_tagout")[0]
        backed = patterns.detect_precursor_patterns(
            text, [make_similar("did not verify") for _ in range(20)], hazard_type="lockout_tagout"
        )[0]
        assert alone.confidence < backed.confidence <= 0.95

    def test_no_history_still_reports_present_patterns(self) -> None:
        text = "The guard removed from the press was never replaced."
        found = patterns.detect_precursor_patterns(text, [], hazard_type="machine_guarding")
        assert [p.pattern_name for p in found] == ["Guard removed or bypassed"]
        assert found[0].evidence_count == 0

    def test_hazard_type_detection_prefers_the_strongest_match(self) -> None:
        text = "No permit was issued and the atmosphere was oxygen deficient with no attendant."
        assert patterns.detect_hazard_type(text) == "confined_space"

    def test_unknown_hazard_falls_back_to_general(self) -> None:
        assert patterns.detect_hazard_type("The quarterly report was filed.") == "general"

    def test_known_precursor_count_includes_general_patterns(self) -> None:
        taxonomy = patterns.taxonomy()
        expected = len(taxonomy["lockout_tagout"]) + len(taxonomy["general"])
        assert patterns.known_precursor_count("lockout_tagout") == expected


class TestRankConfidence:
    """FlashRank orders well but its magnitudes are meaningless, so rank is used."""

    def test_confidence_decays_down_the_ranking(self) -> None:
        scores = [retrieval.rank_confidence(rank) for rank in range(6)]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] == 0.9

    def test_top_results_clear_the_violation_floor_and_the_tail_does_not(self) -> None:
        floor = retrieval.VIOLATION_CONFIDENCE_FLOOR
        assert retrieval.rank_confidence(0) > floor
        assert retrieval.rank_confidence(4) > floor
        assert retrieval.rank_confidence(5) < floor

    def test_confidence_never_goes_negative(self) -> None:
        assert retrieval.rank_confidence(999) == retrieval.RANK_CONFIDENCE_MIN


class TestClauseFamilies:
    @pytest.mark.parametrize(
        ("citation", "family"),
        [
            ("OSHA 29 CFR 1910.147", "lockout_tagout"),
            ("OSHA 29 CFR 1910.146", "confined_space"),
            ("29 CFR 1926.501", "fall_protection"),
            ("29 CFR 1910.1200", "hazcom"),
            ("OSH Act Section 5(a)(1)", "general_duty_clause"),
            ("Some unrecognised local ordinance", "general_duty_clause"),
        ],
    )
    def test_citation_maps_to_weight_family(self, citation: str, family: str) -> None:
        assert retrieval.clause_family(citation) == family

    def test_low_confidence_clauses_are_not_counted_as_violations(self) -> None:
        clauses = [
            RegulatoryClause(
                clause_id="a",
                regulation_name="OSHA 29 CFR 1910.147",
                section="(c)(4)",
                clause_text="...",
                violation_confidence=0.9,
                relevance_explanation="",
            ),
            RegulatoryClause(
                clause_id="b",
                regulation_name="OSHA 29 CFR 1910.22",
                section="(a)",
                clause_text="...",
                violation_confidence=0.1,
                relevance_explanation="",
            ),
        ]
        assert retrieval.violated_clause_families(clauses) == ["lockout_tagout"]


class TestCorrectiveActions:
    async def test_templates_are_sorted_and_deduplicated(self) -> None:
        result = await actions.generate_corrective_actions("lockout_tagout")
        order = [Urgency.IMMEDIATE, Urgency.SHORT_TERM, Urgency.LONG_TERM]
        positions = [order.index(action.urgency) for action in result]
        assert positions == sorted(positions)
        assert result[0].urgency is Urgency.IMMEDIATE
        assert len({action.action for action in result}) == len(result)

    async def test_unknown_hazard_without_llm_still_returns_general_controls(self) -> None:
        result = await actions.generate_corrective_actions(
            "no_such_hazard", precursors=[], clauses=[], summary="something happened"
        )
        assert result
        assert all(action.rationale for action in result)


class TestEntityExtraction:
    """The entity ruler and the LLM discovery pass that covers what it cannot know."""

    REPORT = (
        "The guard removed from the hydraulic press was never replaced. Ammonia vapors "
        "were present near the conveyor. The technician did not verify the isolation "
        "and the disconnect was left closed."
    )

    def test_ruler_finds_domain_entities_without_a_statistical_model(self) -> None:
        found = parsing.spacy_entities(self.REPORT)
        by_type = {(e.entity_type.value, e.text.lower()) for e in found}
        assert ("EQUIPMENT", "press") in by_type
        assert ("CHEMICAL", "ammonia") in by_type
        assert ("UNSAFE_ACT", "did not verify") in by_type, "multi-token patterns must match"
        assert all(e.source == "spacy" for e in found)
        assert all(e.confidence == 0.9 for e in found)

    def test_entities_are_deduplicated(self) -> None:
        found = parsing.spacy_entities("press press press conveyor")
        assert len(found) == len({e.text.lower() for e in found})

    async def test_llm_adds_entities_the_dictionary_cannot_cover(self, monkeypatch) -> None:
        _install_llm(monkeypatch, {"disconnect": "EQUIPMENT", "isolation": "CONDITION"})
        found = await parsing.extract_hazard_entities(self.REPORT)
        discovered = {e.text.lower(): e for e in found if e.source == "llm"}
        assert "disconnect" in discovered
        assert discovered["disconnect"].confidence == 0.75
        # The dictionary hits are still there, still marked as such.
        assert any(e.source == "spacy" and e.text.lower() == "press" for e in found)

    async def test_entities_not_present_in_the_document_are_rejected(self, monkeypatch) -> None:
        _install_llm(monkeypatch, {"a reactor that was never mentioned": "EQUIPMENT"})
        found = await parsing.extract_hazard_entities(self.REPORT)
        assert all("never mentioned" not in e.text for e in found)

    async def test_llm_does_not_duplicate_what_the_ruler_already_found(self, monkeypatch) -> None:
        _install_llm(monkeypatch, {"Ammonia": "CHEMICAL", "press": "EQUIPMENT"})
        found = await parsing.extract_hazard_entities(self.REPORT)
        assert len(found) == len({e.text.lower() for e in found})
        assert not [e for e in found if e.source == "llm"]

    async def test_without_an_llm_the_ruler_result_stands(self, monkeypatch) -> None:
        monkeypatch.setattr(llm, "_providers", lambda *, fast: [])
        found = await parsing.extract_hazard_entities(self.REPORT)
        assert found
        assert all(e.source == "spacy" for e in found)


def _install_llm(monkeypatch, entities: dict[str, str]) -> None:
    overrides = {
        "_EntityDiscovery": {
            "entities": [{"text": text, "entity_type": kind} for text, kind in entities.items()]
        },
        "_Verification": {"keep": []},
    }
    monkeypatch.setattr(llm, "_providers", lambda *, fast: [("fake", FakeLLM(overrides, "unused"))])


class TestIndustryFilterDoesNotStarveRetrieval:
    """Industry is inferred and often unknown, so it must narrow, never starve."""

    @staticmethod
    def _chunk(index: int) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=f"c{index}",
            text="the crew did not verify isolation",
            score=0.5,
            source_document=f"report-{index}.pdf",
        )

    def _patch(self, monkeypatch, by_metadata: dict[str | None, int]):
        """Stub hybrid_search to return N chunks depending on the filter used."""
        calls: list[dict | None] = []

        async def fake(_collection, _query, *, k=8, metadata=None, **_):
            calls.append(metadata)
            industry = (metadata or {}).get("industry")
            return [self._chunk(i) for i in range(by_metadata.get(industry, 0))]

        monkeypatch.setattr(retrieval, "hybrid_search", fake)
        return calls

    async def test_a_well_populated_industry_is_used_as_a_filter(self, monkeypatch) -> None:
        calls = self._patch(monkeypatch, {"chemical": 8})
        found = await retrieval.hybrid_search_incidents("q", industry="chemical", k=8)
        assert len(found) == 8
        assert calls == [{"industry": "chemical"}], "should not need the unfiltered retry"

    async def test_a_starved_filter_falls_back_to_every_industry(self, monkeypatch) -> None:
        calls = self._patch(monkeypatch, {"manufacturing": 1, None: 6})
        found = await retrieval.hybrid_search_incidents("q", industry="manufacturing", k=8)
        assert len(found) == 6, "the unfiltered retry should supply the results"
        assert calls == [{"industry": "manufacturing"}, None]

    async def test_an_empty_filter_falls_back(self, monkeypatch) -> None:
        calls = self._patch(monkeypatch, {"mining": 0, None: 8})
        assert len(await retrieval.hybrid_search_incidents("q", industry="mining", k=8)) == 8
        assert calls[-1] is None

    async def test_no_industry_searches_unfiltered_once(self, monkeypatch) -> None:
        calls = self._patch(monkeypatch, {None: 8})
        await retrieval.hybrid_search_incidents("q", industry=None, k=8)
        assert calls == [None]


class TestSeverityNegation:
    """A report saying nobody was hurt must not read as its own worst outcome."""

    @pytest.mark.parametrize(
        "text",
        [
            "There were no fatalities.",
            "No injuries were reported.",
            "The incident resulted in no injuries or fatalities.",
            "No fatalities, injuries or property damage occurred.",
            "The release was contained without injury.",
        ],
    )
    def test_negated_outcomes_read_as_low_not_critical(self, text: str) -> None:
        # "no fatalities" contains "fatal"; a plain substring search called this CRITICAL.
        assert scoring.classify_severity_by_rules(text) is SeverityTier.LOW

    def test_a_real_outcome_after_a_negated_one_still_counts(self) -> None:
        text = "No fatalities occurred, but one worker suffered an amputation."
        assert scoring.classify_severity_by_rules(text) is SeverityTier.HIGH

    def test_negation_does_not_mask_a_stated_death(self) -> None:
        text = "There were no injuries to the public. One employee was pronounced dead."
        assert scoring.classify_severity_by_rules(text) is SeverityTier.CRITICAL

    def test_counts_still_override_the_text(self) -> None:
        assert (
            scoring.classify_severity_by_rules("No injuries reported.", fatality_count=1)
            is SeverityTier.CRITICAL
        )

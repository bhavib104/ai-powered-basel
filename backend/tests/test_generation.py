"""Generation tests: deterministic, evidence-grounded answers."""

from __future__ import annotations

from app.providers.llm_mock import MockLLM
from app.services import generation


def test_deterministic_answer_cites_evidence() -> None:
    evidence = [
        {
            "source": "Basel capital rules",
            "page": 4,
            "section": "Credit Risk",
            "text": "Banks must hold capital against credit risk.",
        }
    ]
    answer = generation.compose_deterministic("What is credit risk?", evidence)
    assert "Basel capital rules" in answer
    assert "page 4" in answer
    assert "Credit Risk" in answer


def test_deterministic_answer_reports_insufficient_evidence() -> None:
    answer = generation.compose_deterministic("Anything?", [])
    assert "insufficient" in answer.lower()


def test_synthesize_with_mock_uses_deterministic_composer() -> None:
    evidence = [
        {"source": "Doc", "page": None, "section": None, "text": "Some passage."}
    ]
    answer = generation.synthesize("Q?", evidence, MockLLM())
    assert "Some passage." in answer
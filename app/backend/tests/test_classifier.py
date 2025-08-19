from __future__ import annotations

from app.classifier import classify_reason, mock_llm_classify


def test_rules_retryable_exact():
    cls = classify_reason("Incorrect NPI")
    assert cls.label == "retryable"
    assert cls.canonical_reason == "Incorrect NPI"


def test_rules_non_retryable_exact():
    cls = classify_reason("Authorization expired")
    assert cls.label == "non-retryable"


def test_heuristic_similarity():
    cls = classify_reason("wrong npi", mode="rules+heuristic")
    assert cls.label == "retryable"


def test_mock_llm_deterministic():
    a = mock_llm_classify("form incomplete")
    b = mock_llm_classify("form incomplete")
    assert a.label == b.label




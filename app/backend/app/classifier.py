from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from rapidfuzz.distance import Levenshtein


RETRYABLE = {
    "Missing modifier",
    "Incorrect NPI",
    "Prior auth required",
}

NON_RETRYABLE = {
    "Authorization expired",
    "Incorrect provider type",
}

SYNONYMS = {
    "prior authorization required": "Prior auth required",
    "missing mod": "Missing modifier",
    "wrong npi": "Incorrect NPI",
}


@dataclass
class Classification:
    label: str  # retryable | non-retryable | ambiguous | unknown
    canonical_reason: Optional[str] = None


def classify_reason(reason: Optional[str], mode: str = "rules+heuristic") -> Classification:
    if reason is None:
        return Classification(label="ambiguous")
    raw = reason.strip()
    low = raw.lower()

    if mode in {"rules", "rules+heuristic"}:
        for known in RETRYABLE:
            if known.lower() in low:
                return Classification(label="retryable", canonical_reason=known)
        for known in NON_RETRYABLE:
            if known.lower() in low:
                return Classification(label="non-retryable", canonical_reason=known)
        for syn, canon in SYNONYMS.items():
            if syn in low:
                return Classification(label="retryable", canonical_reason=canon)

    if mode in {"heuristic", "rules+heuristic"}:
        # fuzzy contains for retryable set
        for known in RETRYABLE:
            if Levenshtein.normalized_similarity(low, known.lower()) >= 0.82:
                return Classification(label="retryable", canonical_reason=known)

    if mode == "mock-llm":
        return mock_llm_classify(raw)

    # ambiguous catch-all
    return Classification(label="ambiguous")


def mock_llm_classify(text: str) -> Classification:
    # Deterministic pseudo LLM: hash prefix
    h = sum(ord(c) for c in text) % 10
    if h < 3:
        return Classification(label="retryable", canonical_reason="Prior auth required")
    if h < 6:
        return Classification(label="non-retryable", canonical_reason="Authorization expired")
    return Classification(label="ambiguous")




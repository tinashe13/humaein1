from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import structlog

from .classifier import classify_reason
from .config import get_settings
from .recommendations import recommend_change
from .utils_normalize import (
    normalize_datetime,
    normalize_status,
    normalize_string,
    title_case_denial,
)


logger = structlog.get_logger(__name__)


@dataclass
class PipelineResult:
    candidates: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    rejections: List[Dict[str, Any]]


def _ensure_artifacts_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def run_pipeline_from_rows(rows: Iterable[Dict[str, Any]], source: str) -> PipelineResult:
    """Run normalization + eligibility pipeline on in-memory rows.

    - Handles malformed rows gracefully by capturing them in rejections.
    - Aggregates metrics by totals and source.
    - Produces candidate recommendations.
    """
    settings = get_settings()

    total = 0
    accepted = 0
    rejected = 0
    flagged = 0
    excluded = 0

    candidates: List[Dict[str, Any]] = []
    rejections: List[Dict[str, Any]] = []

    for raw in rows:
        total += 1
        try:
            # Normalize
            if source == "alpha":
                claim_id = normalize_string(raw.get("claim_id")) or ""
                patient_id = normalize_string(raw.get("patient_id")) or None
                procedure_code = normalize_string(raw.get("procedure_code")) or None
                denial_reason = title_case_denial(normalize_string(raw.get("denial_reason")))
                status = normalize_status(raw.get("status", ""))
                submitted_at = normalize_datetime(raw.get("submitted_at", ""))
            elif source == "beta":
                claim_id = normalize_string(raw.get("id")) or ""
                patient_id = normalize_string(raw.get("member")) or None
                procedure_code = normalize_string(raw.get("code")) or None
                denial_reason = title_case_denial(normalize_string(raw.get("error_msg")))
                status = normalize_status(raw.get("status", ""))
                submitted_at = normalize_datetime(raw.get("date", ""))
            else:
                raise ValueError("unknown source system")

            if not claim_id:
                raise ValueError("claim_id required")

            accepted += 1

            # Eligibility
            cls = classify_reason(denial_reason)
            ref_date = settings.eligibility_reference_date
            eligible = (
                status == "denied"
                and bool(patient_id)
                and (ref_date - submitted_at.date()).days > 7
                and cls.label == "retryable"
                and bool(cls.canonical_reason)
            )

            if eligible:
                flagged += 1
                reason = cls.canonical_reason or ""
                candidates.append(
                    {
                        "claim_id": claim_id,
                        "resubmission_reason": reason,
                        "source_system": source,
                        "recommended_changes": recommend_change(reason),
                    }
                )
            else:
                excluded += 1
        except Exception as exc:  # noqa: BLE001
            rejected += 1
            rejections.append({"raw": raw, "reason": str(exc)})

    metrics = {
        "processed": total,
        "accepted": accepted,
        "rejected": rejected,
        "flagged": flagged,
        "excluded": excluded,
        "by_source": {source: {"processed": total, "flagged": flagged, "rejected": rejected}},
        "generated_at": datetime.utcnow().isoformat(),
    }

    return PipelineResult(candidates=candidates, metrics=metrics, rejections=rejections)


def save_artifacts(result: PipelineResult) -> None:
    """Write artifacts to disk in the configured artifacts directory."""
    artifacts_dir = get_settings().artifacts_dir
    _ensure_artifacts_dir(artifacts_dir)
    # candidates json (pretty formatted)
    with open(os.path.join(artifacts_dir, "resubmission_candidates.json"), "w", encoding="utf-8") as f:
        json.dump(result.candidates, f, ensure_ascii=False, indent=2)
    # metrics json (pretty formatted)
    with open(os.path.join(artifacts_dir, "resubmission_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(result.metrics, f, ensure_ascii=False, indent=2)
    # rejections jsonl
    with open(os.path.join(artifacts_dir, "rejections.log.jsonl"), "w", encoding="utf-8") as f:
        for r in result.rejections:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    # also provide pretty aggregated rejections array for easy reading
    with open(os.path.join(artifacts_dir, "rejections.json"), "w", encoding="utf-8") as f:
        json.dump(result.rejections, f, ensure_ascii=False, indent=2)


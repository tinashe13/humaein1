from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import structlog

from ..config import get_settings
from ..db import get_db
from ..metrics import processed_records, ingestion_latency
from ..schemas import DatasetCreateResponse, NormalizedClaimIn
from ..utils_normalize import (
    normalize_datetime,
    normalize_status,
    normalize_string,
    title_case_denial,
)
from ..classifier import classify_reason
from ..recommendations import recommend_change


router = APIRouter(prefix="/datasets", tags=["datasets"])
logger = structlog.get_logger(__name__)


@router.get("/health")
def health_check():
    return {"status": "ok", "message": "Datasets API is working"}


def detect_source(filename: str, provided: str | None) -> str:
    if provided:
        return provided
    if filename.endswith(".csv"):
        return "alpha"
    if filename.endswith(".json"):
        return "beta"
    return "unknown"


# POST /datasets — upload a dataset file and trigger normalization/classification
# Supports both trailing-slash and non-trailing-slash to avoid 307 redirect loops.
@router.post("/", response_model=DatasetCreateResponse)
@router.post("", response_model=DatasetCreateResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    source_system: str | None = Form(None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    settings = get_settings()
    size_limit = settings.max_upload_mb * 1024 * 1024
    try:
        data = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    if len(data) > size_limit:
        raise HTTPException(status_code=413, detail="File too large")

    src = detect_source(file.filename, source_system)
    db = get_db()

    # Create a dataset document for auditability and progress tracking
    dataset_doc = {
        "filename": file.filename,
        "source_system": src,
        "uploaded_by": None,
        "uploaded_at": datetime.utcnow(),
        "record_count": 0,
        "metrics_json": None,
    }

    # Time the ingestion end-to-end using a Prometheus histogram
    with ingestion_latency.time():
        try:
            dataset_id = db["datasets"].insert_one(dataset_doc).inserted_id

            count_ok = 0
            count_rej = 0

            if src == "alpha" and file.filename.endswith(".csv"):
                text = data.decode("utf-8", errors="replace")
                reader = csv.DictReader(io.StringIO(text))
                for row in reader:
                    ok = _process_row_alpha(row, str(dataset_id), db)
                    if ok:
                        count_ok += 1
                    else:
                        count_rej += 1
            elif src == "beta" and file.filename.endswith(".json"):
                try:
                    items = json.loads(data)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid JSON")
                if not isinstance(items, list):
                    raise HTTPException(status_code=400, detail="JSON must be an array of objects")
                for obj in items:
                    ok = _process_row_beta(obj, str(dataset_id), db)
                    if ok:
                        count_ok += 1
                    else:
                        count_rej += 1
            else:
                raise HTTPException(status_code=400, detail="Unsupported file for detected source")

            # Update dataset metrics and emit counters
            db["datasets"].update_one({"_id": dataset_id}, {"$set": {"record_count": count_ok}})
            processed_records.labels(source_system=src, result="accepted").inc(count_ok)
            processed_records.labels(source_system=src, result="rejected").inc(count_rej)

            logger.info(
                "dataset_ingested",
                dataset_id=str(dataset_id),
                filename=file.filename,
                source_system=src,
                accepted=count_ok,
                rejected=count_rej,
            )

            return DatasetCreateResponse(
                id=str(dataset_id), filename=file.filename, source_system=src, record_count=count_ok, metrics={"rejected": count_rej}
            )
        except HTTPException:
            # Re-raise known HTTP errors untouched
            raise
        except Exception as exc:  # noqa: BLE001
            # Log unexpected errors and surface a generic message
            logger.exception("dataset_ingestion_failed", filename=file.filename, source_system=src)
            raise HTTPException(status_code=500, detail="Failed to ingest dataset") from exc


def _persist_claim(norm: NormalizedClaimIn, dataset_id: str, db) -> None:  # type: ignore[no-untyped-def]
    existing = db["claims"].find_one({
        "dataset_id": dataset_id,
        "claim_id": norm.claim_id,
        "source_system": norm.source_system,
    })

    denial = norm.denial_reason
    classification = classify_reason(denial)

    eligibility = False
    eligibility_reason = None
    exclusion_reason = None

    ref_date = get_settings().eligibility_reference_date
    if (
        norm.status == "denied"
        and norm.patient_id
        and (ref_date - norm.submitted_at.date()).days > 7
    ):
        if classification.label == "retryable" and classification.canonical_reason:
            eligibility = True
            eligibility_reason = classification.canonical_reason
        elif classification.label == "non-retryable":
            exclusion_reason = classification.canonical_reason
        else:
            exclusion_reason = "Ambiguous"
    else:
        exclusion_reason = "Not eligible by rules"

    doc = {
        "dataset_id": dataset_id,
        "claim_id": norm.claim_id,
        "patient_id": norm.patient_id,
        "procedure_code": norm.procedure_code,
        "denial_reason": denial,
        "status": norm.status,
        "submitted_at": norm.submitted_at,
        "source_system": norm.source_system,
        "raw_payload": norm.raw_payload,
        "eligibility": eligibility,
        "eligibility_reason": eligibility_reason,
        "exclusion_reason": exclusion_reason,
        "ingested_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    if existing:
        db["claims"].update_one({"_id": existing["_id"]}, {"$set": doc})
    else:
        db["claims"].insert_one(doc)


def _process_row_alpha(row: dict[str, Any], dataset_id: str, db) -> bool:  # type: ignore[no-untyped-def]
    try:
        norm = NormalizedClaimIn(
            claim_id=normalize_string(row.get("claim_id")) or "",
            patient_id=normalize_string(row.get("patient_id")) or None,
            procedure_code=normalize_string(row.get("procedure_code")) or None,
            denial_reason=title_case_denial(normalize_string(row.get("denial_reason"))),
            status=normalize_status(row.get("status", "")),
            submitted_at=normalize_datetime(row.get("submitted_at", "")),
            source_system="alpha",
            raw_payload=row,
        )
        if norm.claim_id == "":
            raise ValueError("claim_id required")
        _persist_claim(norm, dataset_id, db)
        return True
    except Exception as exc:  # noqa: BLE001
        db["rejections"].insert_one({
            "dataset_id": dataset_id,
            "raw_payload": row,
            "reason": str(exc),
            "created_at": datetime.utcnow(),
        })
        return False


def _process_row_beta(obj: dict[str, Any], dataset_id: str, db) -> bool:  # type: ignore[no-untyped-def]
    try:
        norm = NormalizedClaimIn(
            claim_id=normalize_string(obj.get("id")) or "",
            patient_id=normalize_string(obj.get("member")) or None,
            procedure_code=normalize_string(obj.get("code")) or None,
            denial_reason=title_case_denial(normalize_string(obj.get("error_msg"))),
            status=normalize_status(obj.get("status", "")),
            submitted_at=normalize_datetime(obj.get("date", "")),
            source_system="beta",
            raw_payload=obj,
        )
        if norm.claim_id == "":
            raise ValueError("claim_id required")
        _persist_claim(norm, dataset_id, db)
        return True
    except Exception as exc:  # noqa: BLE001
        db["rejections"].insert_one({
            "dataset_id": dataset_id,
            "raw_payload": obj,
            "reason": str(exc),
            "created_at": datetime.utcnow(),
        })
        return False


# List datasets (supports both trailing and non-trailing slash)
@router.get("/")
@router.get("")
def list_datasets():  # type: ignore[no-untyped-def]
    db = get_db()
    rows = list(db["datasets"].find().sort("uploaded_at", -1))
    for r in rows:
        r["id"] = str(r.pop("_id"))
    logger.info("datasets_listed", count=len(rows))
    return rows


# Fetch claims for a dataset (minimal filters for now)
@router.get("/{dataset_id}/claims")
def dataset_claims(dataset_id: str):  # type: ignore[no-untyped-def]
    db = get_db()
    items = list(db["claims"].find({"dataset_id": str(dataset_id)}))
    for c in items:
        c["id"] = str(c.pop("_id"))
    logger.info("claims_listed", dataset_id=str(dataset_id), count=len(items))
    return items


# Generate resubmission candidates and optionally stream as CSV
@router.get("/{dataset_id}/candidates")
def dataset_candidates(dataset_id: str, format: str | None = None):  # type: ignore[no-untyped-def]
    from fastapi.responses import StreamingResponse

    db = get_db()
    items = list(db["claims"].find({"dataset_id": str(dataset_id), "eligibility": True}))
    results = []
    for c in items:
        reason = c.get("eligibility_reason") or ""
        results.append({
            "claim_id": c["claim_id"],
            "resubmission_reason": reason,
            "source_system": c["source_system"],
            "recommended_changes": recommend_change(reason) if reason else "Review claim details and resubmit if appropriate",
        })

    # Persist JSON export
    settings = get_settings()
    os.makedirs(settings.data_dir, exist_ok=True)
    out_path = os.path.join(settings.data_dir, "resubmission_candidates.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, separators=(",", ":"))

    logger.info("candidates_generated", dataset_id=str(dataset_id), count=len(results))

    if format == "csv":
        def gen():  # type: ignore[no-untyped-def]
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["claim_id", "resubmission_reason", "source_system", "recommended_changes"])
            writer.writeheader()
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            for row in results:
                writer.writerow(row)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
        return StreamingResponse(gen(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=candidates.csv"})

    return results


@router.get("/{dataset_id}/rejections")
def dataset_rejections(dataset_id: str):  # type: ignore[no-untyped-def]
    from fastapi.responses import StreamingResponse

    db = get_db()
    rows = list(db["rejections"].find({"dataset_id": str(dataset_id)}))

    def gen():  # type: ignore[no-untyped-def]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "raw_payload", "reason", "created_at"])
        writer.writeheader()
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        for r in rows:
            writer.writerow({
                "id": str(r.get("_id")),
                "raw_payload": json.dumps(r.get("raw_payload")),
                "reason": r.get("reason"),
                "created_at": r.get("created_at").isoformat() if r.get("created_at") else "",
            })
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    return StreamingResponse(gen(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=rejections.csv"})


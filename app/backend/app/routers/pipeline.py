from __future__ import annotations

import csv
import io
import json
from typing import Any, List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
import structlog

from ..core import PipelineResult, run_pipeline_from_rows, save_artifacts
from ..config import get_settings


router = APIRouter(prefix="/pipeline", tags=["pipeline"])
logger = structlog.get_logger(__name__)


@router.post("/run")
async def run_pipeline(file: UploadFile | None = File(default=None)):  # type: ignore[no-untyped-def]
    """Run the pipeline on an uploaded CSV or JSON array.

    Returns candidates, metrics, and rejections_count. Always writes artifacts.
    """
    rows: List[dict[str, Any]]
    source = "unknown"

    if file is None:
        raise HTTPException(status_code=400, detail="file is required")

    try:
        data = await file.read()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Error reading file: {exc}") from exc

    filename = file.filename or ""
    if filename.endswith(".csv"):
        source = "alpha"
        text = data.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    elif filename.endswith(".json"):
        source = "beta"
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Invalid JSON") from exc
        if not isinstance(payload, list):
            raise HTTPException(status_code=400, detail="JSON must be an array of objects")
        rows = payload
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    result: PipelineResult = run_pipeline_from_rows(rows, source)
    save_artifacts(result)

    logger.info(
        "pipeline_completed",
        processed=result.metrics.get("processed"),
        flagged=result.metrics.get("flagged"),
        rejected=result.metrics.get("rejected"),
    )

    return {
        "candidates": result.candidates,
        "metrics": result.metrics,
        "rejections_count": len(result.rejections),
    }


@router.get("/last")
def last_run():  # type: ignore[no-untyped-def]
    """Return last artifacts if present."""
    import os
    from ..config import get_settings

    settings = get_settings()
    art = settings.artifacts_dir
    try:
        with open(os.path.join(art, "resubmission_candidates.json"), "r", encoding="utf-8") as f:
            candidates = json.load(f)
    except FileNotFoundError:
        candidates = []
    try:
        with open(os.path.join(art, "resubmission_metrics.json"), "r", encoding="utf-8") as f:
            metrics = json.load(f)
    except FileNotFoundError:
        metrics = {}
    try:
        with open(os.path.join(art, "rejections.log.jsonl"), "r", encoding="utf-8") as f:
            rejections_count = sum(1 for _ in f)
    except FileNotFoundError:
        rejections_count = 0

    return {"candidates": candidates, "metrics": metrics, "rejections_count": rejections_count}


@router.get("/download/candidates.json")
def download_candidates():  # type: ignore[no-untyped-def]
    """Download pretty-formatted candidates JSON."""
    import os
    art = get_settings().artifacts_dir
    path = os.path.join(art, "resubmission_candidates.json")
    return FileResponse(path=path, media_type="application/json", filename="resubmission_candidates.json")


@router.get("/download/metrics.json")
def download_metrics():  # type: ignore[no-untyped-def]
    import os
    art = get_settings().artifacts_dir
    path = os.path.join(art, "resubmission_metrics.json")
    return FileResponse(path=path, media_type="application/json", filename="resubmission_metrics.json")


@router.get("/download/rejections.jsonl")
def download_rejections_log():  # type: ignore[no-untyped-def]
    import os
    art = get_settings().artifacts_dir
    path = os.path.join(art, "rejections.log.jsonl")
    return FileResponse(path=path, media_type="text/plain", filename="rejections.log.jsonl")


@router.get("/download/rejections.json")
def download_rejections_json():  # type: ignore[no-untyped-def]
    import os
    art = get_settings().artifacts_dir
    path = os.path.join(art, "rejections.json")
    return FileResponse(path=path, media_type="application/json", filename="rejections.json")


from __future__ import annotations

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


router = APIRouter()

processed_records = Counter(
    "claims_processed_total",
    "Total processed records",
    labelnames=("source_system", "result"),
)

ingestion_latency = Histogram(
    "ingestion_latency_seconds",
    "Latency of ingestion processing in seconds",
)

classifier_decisions = Counter(
    "classifier_decisions_total",
    "Classifier decisions by label",
    labelnames=("label", "mode"),
)


@router.get("/api/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def instrument_app(app) -> None:  # type: ignore[no-untyped-def]
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        return response




from __future__ import annotations

from prefect import flow, task
from sqlmodel import select

from .db import get_session
from .models import Dataset, Claim
from .classifier import classify_reason
from .config import get_settings


@task
def task_classify(dataset_id: int) -> int:
    settings = get_settings()
    updated = 0
    with get_session() as session:
        items = session.exec(select(Claim).where(Claim.dataset_id == dataset_id)).all()
        for c in items:
            cls = classify_reason(c.denial_reason, mode=settings.classifier_mode)
            if c.status == "denied" and c.patient_id and c.submitted_at.date() < settings.eligibility_reference_date:
                c.eligibility = cls.label == "retryable" and bool(cls.canonical_reason)
                c.eligibility_reason = cls.canonical_reason if c.eligibility else None
                c.exclusion_reason = None if c.eligibility else (cls.canonical_reason or "Ambiguous")
            else:
                c.eligibility = False
                c.eligibility_reason = None
                c.exclusion_reason = "Not eligible by rules"
            session.add(c)
            updated += 1
        session.commit()
    return updated


@flow
def flow_ingest_and_classify(dataset_id: int) -> dict[str, int]:
    updated = task_classify(dataset_id)
    return {"classified": updated}




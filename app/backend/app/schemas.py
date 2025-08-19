from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


Status = Literal["approved", "denied"]


class NormalizedClaimIn(BaseModel):
    claim_id: str
    patient_id: Optional[str]
    procedure_code: Optional[str]
    denial_reason: Optional[str]
    status: Status
    submitted_at: datetime
    source_system: str
    raw_payload: Optional[dict[str, Any]] = None


class DatasetCreateResponse(BaseModel):
    id: str
    filename: str
    source_system: str
    record_count: int
    metrics: dict[str, Any] = Field(default_factory=dict)


class CandidateOut(BaseModel):
    claim_id: str
    resubmission_reason: str
    source_system: str
    recommended_changes: str




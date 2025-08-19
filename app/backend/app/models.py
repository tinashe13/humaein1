from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    pass


class Dataset(SQLModel, table=True):
    __tablename__ = "dataset"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    source_system: str
    uploaded_by: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    record_count: int = 0
    metrics_json: Optional[str] = None

    claims: List["Claim"] = Relationship(back_populates="dataset")
    rejections: List["Rejection"] = Relationship(back_populates="dataset")


class Claim(SQLModel, table=True):
    __tablename__ = "claim"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id")

    claim_id: str
    patient_id: Optional[str] = None
    procedure_code: Optional[str] = None
    denial_reason: Optional[str] = None
    status: str
    submitted_at: datetime
    source_system: str

    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    raw_payload: Optional[str] = None

    eligibility: bool = False
    eligibility_reason: Optional[str] = None
    exclusion_reason: Optional[str] = None

    dataset: Optional["Dataset"] = Relationship(back_populates="claims")


class Rejection(SQLModel, table=True):
    __tablename__ = "rejection"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id")
    raw_payload: str
    reason: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    dataset: Optional["Dataset"] = Relationship(back_populates="rejections")


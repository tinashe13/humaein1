from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings
from ..db import get_db
from ..classifier import classify_reason


router = APIRouter(prefix="/reclassify", tags=["classifier"])


@router.post("/")
def reclassify(dataset_id: str, mode: str | None = None):  # type: ignore[no-untyped-def]
    settings = get_settings()
    mode_eff = mode or settings.classifier_mode
    updated = 0
    db = get_db()
    items = list(db["claims"].find({"dataset_id": str(dataset_id)}))
    for c in items:
        cls = classify_reason(c.get("denial_reason"), mode=mode_eff)
        if (
            c.get("status") == "denied"
            and c.get("patient_id")
            and c.get("submitted_at")
            and c["submitted_at"].date() < settings.eligibility_reference_date
        ):
            if cls.label == "retryable" and cls.canonical_reason:
                c["eligibility"] = True
                c["eligibility_reason"] = cls.canonical_reason
                c["exclusion_reason"] = None
            elif cls.label == "non-retryable":
                c["eligibility"] = False
                c["eligibility_reason"] = None
                c["exclusion_reason"] = cls.canonical_reason
            else:
                c["eligibility"] = False
                c["eligibility_reason"] = None
                c["exclusion_reason"] = "Ambiguous"
            updated += 1
        else:
            c["eligibility"] = False
            c["eligibility_reason"] = None
            c["exclusion_reason"] = "Not eligible by rules"
        db["claims"].update_one({"_id": c["_id"]}, {"$set": {
            "eligibility": c["eligibility"],
            "eligibility_reason": c.get("eligibility_reason"),
            "exclusion_reason": c.get("exclusion_reason"),
        }})
    return {"updated": updated, "mode": mode_eff}




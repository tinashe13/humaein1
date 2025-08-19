from __future__ import annotations

TEMPLATES = {
    "Missing modifier": "Add the appropriate billing modifier and resubmit",
    "Incorrect NPI": "Review NPI number and resubmit",
    "Prior auth required": "Obtain prior authorization and include reference number",
}


def recommend_change(reason: str) -> str:
    return TEMPLATES.get(reason, "Review claim details and resubmit if appropriate")




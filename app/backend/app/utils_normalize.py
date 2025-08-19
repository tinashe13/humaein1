from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any, Dict, Iterable, Iterator, Tuple

from dateutil import parser

WHITESPACE_RE = re.compile(r"\s+")


def normalize_string(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if trimmed == "":
        return None
    collapsed = WHITESPACE_RE.sub(" ", trimmed)
    return collapsed


def normalize_status(value: str) -> str:
    v = (value or "").strip().lower()
    if v not in {"approved", "denied"}:
        raise ValueError(f"unknown status: {value}")
    return v


def normalize_datetime(value: str) -> datetime:
    dt = parser.isoparse(value) if "T" in value or "+" in value else parser.parse(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def title_case_denial(value: str | None) -> str | None:
    if value is None:
        return None
    text = normalize_string(value)
    if text is None:
        return None
    # Preserve NPI acronym
    text = text.replace("npi", "NPI").replace("Npi", "NPI")
    words = [w.capitalize() if w.upper() != "NPI" else "NPI" for w in text.split(" ")]
    return " ".join(words)


def serialize_raw(obj: dict[str, Any]) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)




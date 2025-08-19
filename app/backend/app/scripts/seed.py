from __future__ import annotations

import json
import os
from pathlib import Path

import httpx


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    data_dir = root / "app" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    alpha_path = data_dir / "emr_alpha.csv"
    beta_path = data_dir / "emr_beta.json"

    # sample alpha
    alpha_path.write_text(
        """claim_id,patient_id,procedure_code,denial_reason,submitted_at,status
A123,P001,99213,Incorrect NPI,2025-07-01,denied
A124,P002,99214,Missing modifier,2025-07-05,denied
A125,,99215,Prior auth required,2025-07-01,denied
""",
        encoding="utf-8",
    )

    # sample beta
    beta_data = [
        {"id": "B200", "member": "P003", "code": "93000", "error_msg": "form incomplete", "date": "2025-06-20", "status": "denied"},
        {"id": "B201", "member": "P004", "code": "93010", "error_msg": None, "date": "2025-06-18", "status": "denied"},
        {"id": "B202", "member": "P005", "code": "93010", "error_msg": "Authorization expired", "date": "2025-06-10", "status": "denied"},
    ]
    beta_path.write_text(json.dumps(beta_data), encoding="utf-8")

    with httpx.Client(timeout=30.0) as client:
        with open(alpha_path, "rb") as f:
            resp = client.post(f"{backend_url}/api/datasets", files={"file": (alpha_path.name, f, "text/csv")}, data={"source_system": "alpha"})
            print("alpha:", resp.status_code, resp.text)
        with open(beta_path, "rb") as f:
            resp = client.post(f"{backend_url}/api/datasets", files={"file": (beta_path.name, f, "application/json")}, data={"source_system": "beta"})
            print("beta:", resp.status_code, resp.text)


if __name__ == "__main__":
    main()




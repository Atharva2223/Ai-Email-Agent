import json
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPROVALS_FILE = PROJECT_ROOT / "data" / "approvals.json"


def _ensure_approvals_file() -> None:
    APPROVALS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not APPROVALS_FILE.exists():
        with open(APPROVALS_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=2)


def load_approvals() -> List[Dict[str, Any]]:
    _ensure_approvals_file()

    with open(APPROVALS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_approvals(approvals: List[Dict[str, Any]]) -> None:
    _ensure_approvals_file()

    with open(APPROVALS_FILE, "w", encoding="utf-8") as file:
        json.dump(approvals, file, indent=2)


def create_approval_request(payload: Dict[str, Any]) -> str:
    approvals = load_approvals()

    approval_id = str(uuid4())
    payload["approval_id"] = approval_id
    payload["status"] = "pending"

    approvals.append(payload)
    save_approvals(approvals)

    return approval_id


def list_pending_approvals() -> List[Dict[str, Any]]:
    approvals = load_approvals()
    return [item for item in approvals if item.get("status") == "pending"]


def update_approval_status(approval_id: str, status: str) -> bool:
    approvals = load_approvals()
    updated = False

    for item in approvals:
        if item.get("approval_id") == approval_id:
            item["status"] = status
            updated = True
            break

    if updated:
        save_approvals(approvals)

    return updated
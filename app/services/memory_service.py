import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_FILE = PROJECT_ROOT / "data" / "memory.json"


def _ensure_memory_file() -> None:
    """
    Create the memory file and parent folder if they do not exist.
    """
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not MEMORY_FILE.exists():
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            json.dump({}, file, indent=2)


def load_memory() -> Dict[str, Any]:
    """
    Load all memory data from the JSON file.
    """
    _ensure_memory_file()

    with open(MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_memory(memory_data: Dict[str, Any]) -> None:
    """
    Save all memory data to the JSON file.
    """
    _ensure_memory_file()

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory_data, file, indent=2)


def get_user_memory(user_email: str) -> Dict[str, Any]:
    """
    Return stored memory for one user.
    """
    memory_data = load_memory()
    return memory_data.get(user_email, {})


def update_user_memory(user_email: str, new_data: Dict[str, Any]) -> None:
    """
    Merge and save memory for one user.
    """
    memory_data = load_memory()

    existing = memory_data.get(user_email, {})
    existing.update(new_data)

    memory_data[user_email] = existing
    save_memory(memory_data)


def append_interaction(user_email: str, interaction: Dict[str, Any]) -> None:
    """
    Append an interaction entry to the user's history.
    """
    memory_data = load_memory()

    user_record = memory_data.get(user_email, {})
    history: List[Dict[str, Any]] = user_record.get("history", [])

    history.append(interaction)
    user_record["history"] = history

    memory_data[user_email] = user_record
    save_memory(memory_data)
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

BRIEFS_DIR = Path("data/briefs")


def _ensure_dir() -> Path:
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    return BRIEFS_DIR


def save_brief(
    study_id: str,
    title: str,
    org: str,
    year: str,
    brief: dict[str, Any],
) -> Path:
    """Persist a generated brief to disk. Returns the saved file path."""
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = str(study_id).replace("/", "_").replace(" ", "_")
    filename = BRIEFS_DIR / f"{safe_id}_{timestamp}.json"
    payload = {
        "study_id": study_id,
        "title": title,
        "organization": org,
        "year": year,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "brief": brief,
    }
    filename.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return filename


def list_briefs() -> list[dict[str, Any]]:
    """Return all saved briefs as a list of dicts, newest first."""
    d = _ensure_dir()
    records = []
    for f in sorted(d.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_filename"] = f.name
            records.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return records


def load_brief(filename: str) -> dict[str, Any] | None:
    """Load a single brief by filename. Returns None if not found."""
    path = BRIEFS_DIR / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def delete_brief(filename: str) -> bool:
    """Delete a brief file. Returns True if deleted."""
    path = BRIEFS_DIR / filename
    if path.exists():
        path.unlink()
        return True
    return False

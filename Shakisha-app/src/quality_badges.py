from __future__ import annotations

from typing import List


def parse_quality_flags(raw: str) -> List[str]:
    if not raw or not isinstance(raw, str):
        return []
    return [x.strip() for x in raw.split(";") if x.strip()]


def quality_level(missing_field_count: int) -> str:
    if missing_field_count <= 0:
        return "good"
    if missing_field_count <= 2:
        return "warning"
    return "critical"


from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchContext:
    donor_id: str | None = None
    program_id: str | None = None


def visibility_filter(context: SearchContext) -> dict[str, Any]:
    allowed: list[dict[str, Any]] = [
        {"content_type": "campaign_report", "visibility": "public"}
    ]
    if context.donor_id:
        allowed.append(
            {"content_type": "donor_receipt", "donor_id": context.donor_id}
        )
    if context.program_id:
        allowed.append(
            {"content_type": "volunteer_reminder", "program_id": context.program_id}
        )
    return {"$or": allowed}

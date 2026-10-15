"""Coded tool for the governance dashboard network.

It reads only data/Gov_Events.csv (synthetic demo data) and returns aggregated counts. A count below
SUPPRESSION_THRESHOLD is replaced by "suppressed". It never returns a row, an event id or any personal detail.

Differencing guard: every aggregate that is released is remembered in sly_data. If a new aggregate and an earlier one
cover overlapping groups of rows and subtracting them would reveal a count below the threshold, the new query is refused.
"""
import csv
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Union

from neuro_san.interfaces.coded_tool import CodedTool

SUPPRESSION_THRESHOLD = 10  # counts below this are never shown; the only place this value is set
SUPPRESSED = "suppressed"
REQUIRED_PHRASE = "synthetic demo data"
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "Gov_Events.csv"
GROUP_FIELDS = ("module", "district", "event_type")


def _rows() -> List[dict]:
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return [dict(r, count=int(r["count"])) for r in csv.DictReader(f)]


def _refusal(reason: str) -> Dict[str, Any]:
    return {"refused": True, "reason": reason, "data_note": f"This is {REQUIRED_PHRASE}."}


class DashboardQuery(CodedTool):
    """Answers aggregate questions over Gov_Events.csv with small-count suppression and a differencing guard."""

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: "group_by": list of up to two of module, district, event_type (optional).
                     "module", "district", "event_type": optional filters (exact match, case-insensitive).
                     "month": "latest" or YYYY-MM (optional).
        :param sly_data: Holds the list of aggregates already released in this session ("released").
        :return: Cells with a count or "suppressed", or a refusal if the query could reveal a small count.
        """
        sly_data["require_phrase"] = REQUIRED_PHRASE
        released: list = sly_data.setdefault("released", [])

        group_by = [g for g in (args.get("group_by") or []) if g in GROUP_FIELDS][:2]
        rows = _rows()
        months = sorted({r["week_start"][:7] for r in rows})
        month = str(args.get("month") or "")
        if month == "latest":
            month = months[-1]
        if month:
            rows = [r for r in rows if r["week_start"].startswith(month)]
        for field in GROUP_FIELDS:
            wanted = str(args.get(field) or "").strip().lower()
            if wanted:
                rows = [r for r in rows if r[field].lower() == wanted]
        if not rows:
            return {"cells": [], "data_note": f"No matching data. This is {REQUIRED_PHRASE}.",
                    "months_available": months}

        groups: Dict[tuple, List[dict]] = {}
        for r in rows:
            groups.setdefault(tuple(r[g] for g in group_by), []).append(r)

        cells = []
        candidate = []  # aggregates that would be released with this answer
        for key, members in sorted(groups.items()):
            total = sum(m["count"] for m in members)
            shown = total if total >= SUPPRESSION_THRESHOLD else SUPPRESSED
            cells.append({"group": dict(zip(group_by, key)), "count": shown})
            if shown != SUPPRESSED:
                candidate.append({"rows": sorted(m["event_id"] for m in members), "value": total})

        # Within one answer a total is only given if no cell is suppressed, so the total cannot be subtracted.
        any_suppressed = any(c["count"] == SUPPRESSED for c in cells)
        if group_by and not any_suppressed:
            all_rows = sorted(m["event_id"] for m in rows)
            grand = sum(m["count"] for m in rows)
            candidate.append({"rows": all_rows, "value": grand})

        by_id = {r["event_id"]: r["count"] for r in _rows()}
        for new in candidate:
            for old in released:
                small, large = sorted((set(new["rows"]), set(old["rows"])), key=len)
                if small < large:
                    diff = sum(by_id[i] for i in large - small)
                    if diff < SUPPRESSION_THRESHOLD:
                        return _refusal(
                            "Answering this together with an earlier answer would let someone subtract one from the "
                            "other and work out a small count that must stay hidden.")

        released.extend(candidate)
        result: Dict[str, Any] = {
            "cells": cells,
            "months_available": months,
            "suppression_threshold": SUPPRESSION_THRESHOLD,
            "data_note": f"This is {REQUIRED_PHRASE}. Counts below {SUPPRESSION_THRESHOLD} are shown as '{SUPPRESSED}'.",
        }
        if group_by:
            result["total"] = candidate[-1]["value"] if not any_suppressed else "withheld because a group is suppressed"
        return result

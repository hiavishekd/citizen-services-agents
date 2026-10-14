"""Coded tools for the health triage network.

They read only data/Health_RedFlags.csv, data/Health_Facilities.csv and data/Helplines.csv. Personal details
(name, phone, village, age band) are kept in sly_data and never returned to the model.
"""
import csv
import re
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Union

from neuro_san.interfaces.coded_tool import CodedTool

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEMO_MARKERS = ("AUTHORED_DEMO", "SYNTHETIC")
PERSONAL_FIELDS = ["name", "phone", "village", "age_band"]

# English keyword hints per rule, a safety net on top of the model's own reading of the symptoms.
KEYWORDS = {
    "HR-01": ["cannot drink", "can't drink", "not drinking", "cannot breastfeed", "not feeding", "vomits everything",
              "vomiting everything", "convulsion", "seizure", "fits", "unconscious", "very sleepy", "unusually sleepy"],
    "HR-02": ["difficulty breathing", "trouble breathing", "breathless", "cannot breathe", "can't breathe",
              "blue lips", "cannot speak", "can't speak"],
    "HR-03": ["fast breathing", "chest pulling", "chest indrawing", "chest in"],
    "HR-04": ["chest pain", "pain spreading", "pain in arm", "pain in jaw"],
    "HR-05": ["face droop", "drooping", "arm weakness", "weak arm", "slurred", "stroke"],
    "HR-06": ["heavy bleeding", "bleeding heavily", "severe headache", "blurred vision"],
    "HR-07": ["fever for 3 days", "fever for three days", "fever for 4 days", "fever for 5 days", "fever since 3 days",
              "fever 3 days", "fever for a week"],
    "HR-08": ["dehydrat", "sunken eyes", "loose motion", "diarrhoea", "diarrhea", "very thirsty"],
}


def _read(name: str) -> list:
    with open(DATA_DIR / f"{name}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _is_demo(row: dict) -> bool:
    return any(m in row.get("data_status", "").upper() for m in DEMO_MARKERS)


class PersonalDetails(CodedTool):
    """Saves personal details into sly_data and reports which fields are known (never their values)."""

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: Any of name, phone, village, age_band.
        :param sly_data: Holds the "personal" dictionary.
        :return: Known and missing field names only.
        """
        personal = sly_data.setdefault("personal", {})
        for key in PERSONAL_FIELDS:
            if args.get(key) not in (None, ""):
                personal[key] = args[key]
        return {"known_fields": sorted(personal), "missing_fields": [k for k in PERSONAL_FIELDS if k not in personal]}


class TriageLookup(CodedTool):
    """Matches symptoms against Health_RedFlags.csv and suggests facilities from Health_Facilities.csv."""

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: "symptoms_en": short English summary of the symptoms with names, places and numbers removed.
                     "age_group": child_under_5, adult, pregnant or other.
        :param sly_data: Reads the "personal" dictionary (only to know the village).
        :return: Red-flag rules with keyword hints, emergency numbers, and facilities.
        """
        text = re.sub(r"[\d+\-()]{6,}", " ", str(args.get("symptoms_en", ""))).lower()
        rules = []
        for row in _read("Health_RedFlags"):
            hits = [k for k in KEYWORDS.get(row["rule_id"], []) if k in text]
            rules.append({
                "rule_id": row["rule_id"],
                "age_group": row["age_group"],
                "symptom_pattern": row["symptom_pattern"],
                "urgency": row["urgency"],
                "recommended_action": row["recommended_action"],
                "keyword_hit": bool(hits),
                "label_as_demo_data": _is_demo(row),
            })
        emergency_detected = any(r["keyword_hit"] and r["urgency"] == "EMERGENCY" for r in rules)

        helplines = {h["helpline_id"]: h for h in _read("Helplines")}
        numbers = [helplines[i]["number_or_contact"] for i in ("H-108", "H-112") if i in helplines]

        village = str(sly_data.get("personal", {}).get("village", "")).lower()
        facilities = sorted(_read("Health_Facilities"), key=lambda r: float(r["distance_km_from_demo_village"]))
        facility_list = [{
            "facility_id": r["facility_id"], "name": r["name"], "type": r["type"],
            "distance_km": r["distance_km_from_demo_village"], "services": r["services"], "hours": r["hours"],
            "ambulance": r["ambulance"], "label_as_demo_data": _is_demo(r),
            "in_person_village": bool(village) and village == r["village_or_town"].lower(),
        } for r in facilities]
        return {
            "emergency_detected_by_keywords": emergency_detected,
            "emergency_numbers": numbers,
            "red_flag_rules": rules,
            "facilities": facility_list,
            "facility_guidance": {"EMERGENCY": "Community Health Centre or District Hospital, by ambulance",
                                  "URGENT": "Primary Health Centre today",
                                  "ROUTINE": "Sub-centre or village health worker"},
            "rule": "Use only these rules, numbers and facilities. Never diagnose. Never name medicines or doses.",
        }

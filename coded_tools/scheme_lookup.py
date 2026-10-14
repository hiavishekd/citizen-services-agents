"""Coded tools for the scheme navigator network.

They read only the CSV files under data/ (Schemes, Helplines, Sources_Registry). The person's profile is kept in
sly_data, so it never has to be repeated in a prompt. Links come only from Sources_Registry.
"""
import csv
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Union

from neuro_san.interfaces.coded_tool import CodedTool

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEMO_MARKERS = ("AUTHORED_DEMO", "SYNTHETIC")
PROFILE_FIELDS = ["age", "state", "occupation", "income_band", "household", "owns_cultivable_land",
                  "income_tax_payer", "bpl_status", "widowed", "language"]


def _read(name: str) -> list:
    with open(DATA_DIR / f"{name}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _norm(url: str) -> str:
    return url.strip().rstrip("/").lower()


def _is_demo(row: dict) -> bool:
    return any(m in row.get("data_status", "").upper() for m in DEMO_MARKERS)


def _yes(value: Any) -> Any:
    """Return True/False for yes/no style answers, None if unknown."""
    text = str(value).strip().lower()
    if text in ("yes", "y", "true", "1", "haan", "हाँ", "हां", "হ্যাঁ"):
        return True
    if text in ("no", "n", "false", "0", "nahi", "नहीं", "না"):
        return False
    return None


class ProfileStore(CodedTool):
    """Saves what the person told us into sly_data and reports what is still unknown."""

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: Any of age, state, occupation, income_band, household, owns_cultivable_land,
                     income_tax_payer, bpl_status, widowed, language.
        :param sly_data: Holds the "profile" dictionary.
        :return: Which profile fields are known (not their values) and which are missing.
        """
        profile = sly_data.setdefault("profile", {})
        for key in PROFILE_FIELDS:
            if args.get(key) not in (None, ""):
                profile[key] = args[key]
        return {"known_fields": sorted(profile), "missing_fields": [k for k in PROFILE_FIELDS if k not in profile]}


class SchemeLookup(CodedTool):
    """Matches the stored profile against Schemes.csv and returns only rows that exist there."""

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: Optional "scheme_id" to return one scheme only.
        :param sly_data: Reads the "profile" dictionary.
        :return: Candidate schemes with fit hints, the official link, documents and helplines.
        """
        profile = sly_data.get("profile", {})
        sources = {r["source_id"]: r for r in _read("Sources_Registry")}
        registry_urls = {_norm(r["url"]): r["url"] for r in sources.values()}
        helplines = _read("Helplines")

        results = []
        for row in _read("Schemes"):
            if args.get("scheme_id") and row["scheme_id"] != args["scheme_id"]:
                continue
            link = registry_urls.get(_norm(row["official_url"]))
            if link is None:
                ids = [s.strip() for s in row["source_ids"].split(";")]
                link = next((sources[i]["url"] for i in ids if i in sources), None)
            fit, reason = self._fit(row["scheme_id"], profile)
            results.append({
                "scheme_id": row["scheme_id"],
                "scheme_name": row["scheme_name"],
                "benefit": row["benefit"],
                "eligibility_rules": row["eligibility_rules"],
                "exclusions": row["exclusions"],
                "documents_needed": row["documents_needed"],
                "how_to_apply": row["how_to_apply"],
                "state_variation_note": row["state_variation_note"],
                "official_link": link,
                "fit": fit,
                "fit_reason": reason,
                "data_status": row["data_status"],
                "label_as_demo_data": _is_demo(row),
                "helplines": self._helplines(row["helpline"], helplines),
            })
        return {"schemes": results, "scheme_count_in_data": len(results),
                "more_schemes_link": sources.get("S33", {}).get("url"),
                "coverage_note": "This sample covers only five central schemes; other schemes exist.",
                "rule": "Recommend only these schemes. Use only official_link as a URL."}

    @staticmethod
    def _helplines(scheme_helpline: str, helplines: list) -> list:
        """Match the scheme's helpline text against Helplines.csv; fall back to the text as written."""
        tokens = [t.split("(")[0].strip() for t in scheme_helpline.split(" or ")]
        found = [h["number_or_contact"] for h in helplines if any(t and t in h["number_or_contact"] for t in tokens)]
        return found or [scheme_helpline]

    @staticmethod
    def _fit(scheme_id: str, p: Dict[str, Any]) -> tuple:
        """Rule-based hint: ('likely' | 'unlikely' | 'check', reason). The model must still explain caveats."""
        age = int(p["age"]) if str(p.get("age", "")).isdigit() else None
        land, tax, bpl, widow = (_yes(p.get(k)) for k in
                                 ("owns_cultivable_land", "income_tax_payer", "bpl_status", "widowed"))
        if scheme_id == "SCH-01":
            professions = ("doctor", "engineer", "lawyer", "advocate", "architect", "chartered accountant")
            if any(w in str(p.get("occupation", "")).lower() for w in professions):
                return "unlikely", "Professionals such as doctors, engineers and lawyers are excluded."
            if land is False:
                return "unlikely", "No cultivable land owned; the scheme needs landholding."
            if tax is True:
                return "unlikely", "Income tax payers are excluded."
            if land is True and tax is False:
                return "likely", "Owns land and is not an income tax payer; e-KYC is required."
            return "check", "Need land ownership and income tax status."
        if scheme_id == "SCH-02":
            return "check", "Eligibility depends on the beneficiary database; send to the official eligibility check."
        if scheme_id == "SCH-03":
            if widow is False or (age is not None and age < 40):
                return "unlikely", "Needs a widow aged 40 or above."
            if widow is True and bpl is True and age is not None and age >= 40:
                return "likely", "Widow aged 40+ in a BPL household; confirm BPL proof and no other pension."
            return "check", "Need widow status, age and BPL status."
        if scheme_id == "SCH-04":
            if age is not None and age < 60:
                return "unlikely", "Needs age 60 or above."
            if bpl is False:
                return "unlikely", "Needs a BPL household."
            if age is not None and age >= 60 and bpl is True:
                return "likely", "Aged 60+ in a BPL household."
            return "check", "Need age and BPL status."
        if scheme_id == "SCH-05":
            return "check", "Only relevant after the death of a BPL household's primary breadwinner."
        return "check", "No rule available."

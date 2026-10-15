"""Reply guard shared by the networks.

The model drafts its reply, passes it here, and sends back exactly what this tool returns. Any link or web address
that is not in data/Sources_Registry.csv is removed, so a wrong link can never reach the person, stored names and numbers are removed, and links copied
from untrusted text (such as a scam message) are never repeated.
"""
import csv
import re
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Set
from typing import Union
from urllib.parse import urlparse

from neuro_san.interfaces.coded_tool import CodedTool

REGISTRY = Path(__file__).resolve().parent.parent / "data" / "Sources_Registry.csv"
REMOVED = "[link removed]"

URL_RE = re.compile(r"(?i)\b(?:https?|hxxps?|ftp)://[^\s<>\"')\]]+")
BARE_RE = re.compile(r"(?i)\b(?:[a-z0-9-]+\.)+(?:in|com|org|net|io|app|xyz|example|info|co|me|link|online|site|top|club|biz)\b")
TRAILING = ".,;:!?*)]}।"


def _norm_url(url: str) -> str:
    return re.sub(r"^https?://", "", url.strip().rstrip("/").lower()).removeprefix("www.")


def _allowed() -> tuple:
    urls: Set[str] = set()
    hosts: Set[str] = set()
    with open(REGISTRY, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            urls.add(_norm_url(row["url"]))
            hosts.add(urlparse(row["url"]).netloc.lower().removeprefix("www."))
    return urls, hosts


def clean_text(text: str) -> tuple:
    """Return (cleaned text, list of removed strings)."""
    urls, hosts = _allowed()
    removed = []

    def fix_url(match: re.Match) -> str:
        raw = match.group(0)
        core = raw.rstrip(TRAILING)
        tail = raw[len(core):]
        if re.match(r"(?i)https?://", core) and _norm_url(core) in urls:
            return core + tail
        removed.append(core)
        return REMOVED + tail

    text = URL_RE.sub(fix_url, text)

    def fix_bare(match: re.Match) -> str:
        word = match.group(0)
        if word.lower().removeprefix("www.") in hosts:
            return word
        removed.append(word)
        return REMOVED

    parts = re.split(r"(\[link removed\])", text)
    text = "".join(p if p == REMOVED else BARE_RE.sub(fix_bare, p) for p in parts)
    return text, removed


def scrub_personal(text: str, sly_data: Dict[str, Any]) -> tuple:
    """Remove stored personal values (names, phone and account numbers) from the reply. Returns (text, count)."""
    count = 0
    for value in sly_data.get("personal", {}).values():
        value = str(value).strip()
        if not value:
            continue
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 6:
            pattern = r"\+?" + r"[\s-]?".join(digits)
        else:
            tokens = [re.escape(t) for t in value.split() if len(t) >= 3]
            pattern = r"\b(?:" + "|".join([re.escape(value)] + tokens) + r")\b" if tokens else re.escape(value)
        text, n = re.subn(pattern, "", text, flags=re.IGNORECASE)
        count += n
    if count:
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"(?im)^(hello|hi|dear|namaste|namaskar|নমস্কার|नमस्ते)[ ,!.]*$", "", text)
        text = re.sub(r"(?i)\b(hello|hi|dear)\s*[,.!]\s*", r"", text)
        text = text.lstrip()
        text = text[:1].upper() + text[1:]
    return text, count


def drop_sentences(text: str, pattern: str) -> str:
    """Drop every sentence or bullet that matches the pattern a network has set in sly_data."""
    if not pattern:
        return text
    regex = re.compile(pattern)
    out = []
    for line in text.split("\n"):
        parts = re.split(r"(?<=[.!?।])\s+", line)
        kept = [p for p in parts if not regex.search(p)]
        if kept or not line.strip():
            out.append(" ".join(kept))
    return "\n".join(out)


class ReplyGuard(CodedTool):
    """Removes every link or web address that is not in Sources_Registry.csv."""

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: "draft_reply": the full reply the model wants to send.
        :param sly_data: Reads the stored "personal" values so they can be removed from the reply.
        :return: "final_reply" to send exactly as given, and how many links were removed.
        """
        cleaned, removed = clean_text(str(args.get("draft_reply", "")))
        cleaned, personal_removed = scrub_personal(cleaned, sly_data)
        cleaned = drop_sentences(cleaned, sly_data.get("drop_sentences_matching"))
        phrase = sly_data.get("require_phrase")
        if phrase and phrase.lower() not in cleaned.lower():
            cleaned = cleaned.rstrip() + f"\n\nNote: this is {phrase}."
        return {"final_reply": cleaned, "links_removed": len(removed), "personal_values_removed": personal_removed}

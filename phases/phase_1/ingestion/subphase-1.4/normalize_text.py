from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"
NORMALIZED_DIR = OUTPUT_DIR / "normalized"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _normalize_whitespace(text: str) -> str:
    # Normalize whitespace but keep newlines meaningful for chunking
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _split_lines(text: str) -> list[str]:
    # Split and keep only non-empty lines
    lines = [ln.strip() for ln in text.split("\n")]
    return [ln for ln in lines if ln]


def _is_boilerplate_candidate(line: str) -> bool:
    """
    Heuristic boilerplate detection for mostly-HTML extracted text.
    Keep conservative to avoid removing real finance facts.
    """
    l = line.lower()

    # Too short or too generic
    if len(l) <= 2:
        return True

    # Common UI / chrome words (seen on many sites)
    chrome_patterns = [
        r"\blog in\b",
        r"\bsign up\b",
        r"\bdownload app\b",
        r"\bcookie\b",
        r"\bprivacy policy\b",
        r"\bterms\b",
        r"\bcontact us\b",
        r"\bdisclaimer\b",
        r"\ball rights reserved\b",
        r"\bhome\b",
        r"\bexplore\b",
        r"\bproducts?\b",
        r"\bcalculator\b",
        r"\bhelp\b",
        r"\bsupport\b",
        r"\babout\b",
    ]
    if any(re.search(p, l) for p in chrome_patterns):
        return True

    # Remove pure menu-ish sequences (many words but no numbers / no punctuation)
    if len(line) < 80 and re.fullmatch(r"[A-Za-z][A-Za-z ]{10,}", line) and not re.search(r"\d", line):
        return True

    return False


SECTION_LABELS = [
    "Expense Ratio",
    "Exit Load",
    "Minimum SIP",
    "Minimum Lump Sum",
    "Benchmark",
    "Risk",
    "Riskometer",
    "Fund Manager",
    "Lock-in",
    "ELSS",
]


def _inject_section_markers(text: str) -> str:
    """
    Add stable markers when label tokens appear, without relying on original HTML headings.
    This helps later chunking find boundaries even in flattened text.
    """
    t = text
    for label in SECTION_LABELS:
        # Insert marker before label when it appears as a word boundary
        t = re.sub(rf"(?<!#)\b{re.escape(label)}\b", f"\n\n## {label}\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


@dataclass(frozen=True)
class NormalizationEntry:
    url: str
    url_id: str
    parsed_path: str
    normalized_path: str | None
    ok: bool
    original_chars: int
    normalized_chars: int
    removed_lines: int
    removed_repeated_lines: int
    flags: list[str]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    parse_report_path = Path(__file__).resolve().parents[1] / "subphase-1.3" / "output" / "parse_report.json"
    parse_report = _read_json(parse_report_path)
    entries = parse_report.get("entries", [])

    # Build global line frequency map to remove repeated chrome across pages.
    # We only consider "short-ish" lines for repetition removal to avoid nuking real content.
    line_doc_freq: dict[str, int] = {}
    entry_lines: dict[str, list[str]] = {}

    for e in entries:
        if not e.get("ok"):
            continue
        parsed_path = e.get("parsed_path")
        url_id = e.get("url_id")
        if not parsed_path or not url_id:
            continue
        txt = Path(parsed_path).read_text(encoding="utf-8", errors="replace")
        txt = _normalize_whitespace(txt)
        lines = _split_lines(txt)
        entry_lines[url_id] = lines
        seen: set[str] = set()
        for ln in lines:
            if len(ln) > 90:
                continue
            key = ln.lower()
            if key in seen:
                continue
            seen.add(key)
            line_doc_freq[key] = line_doc_freq.get(key, 0) + 1

    # Anything appearing in >= 3 docs is probably global nav/footer boilerplate for our small corpus.
    repeated_threshold = 3 if len(entry_lines) >= 5 else max(2, len(entry_lines))
    repeated_lines = {k for (k, c) in line_doc_freq.items() if c >= repeated_threshold}

    normalized_entries: list[NormalizationEntry] = []

    for e in entries:
        url = e.get("url")
        url_id = e.get("url_id")
        parsed_path = e.get("parsed_path")
        if not (e.get("ok") and url and url_id and parsed_path):
            normalized_entries.append(
                NormalizationEntry(
                    url=url or "",
                    url_id=url_id or "",
                    parsed_path=parsed_path or "",
                    normalized_path=None,
                    ok=False,
                    original_chars=0,
                    normalized_chars=0,
                    removed_lines=0,
                    removed_repeated_lines=0,
                    flags=["missing_or_failed_parse"],
                )
            )
            continue

        raw = Path(parsed_path).read_text(encoding="utf-8", errors="replace")
        original_chars = len(raw)
        text = _normalize_whitespace(raw)
        lines = _split_lines(text)

        kept: list[str] = []
        removed_lines = 0
        removed_repeated_lines = 0

        for ln in lines:
            low = ln.lower()
            if low in repeated_lines:
                removed_lines += 1
                removed_repeated_lines += 1
                continue
            if _is_boilerplate_candidate(ln):
                removed_lines += 1
                continue
            kept.append(ln)

        cleaned = "\n".join(kept)
        cleaned = _normalize_whitespace(cleaned)
        cleaned = _inject_section_markers(cleaned)

        flags: list[str] = []
        if not cleaned:
            flags.append("empty_after_cleaning")
        if len(cleaned) < 800:
            flags.append("too_short_after_cleaning")
        removed_ratio = (removed_lines / max(1, len(lines))) if lines else 0.0
        if removed_ratio >= 0.6:
            flags.append("high_boilerplate_removed_ratio")

        out_path = NORMALIZED_DIR / f"{url_id}.txt"
        out_path.write_text(cleaned + "\n", encoding="utf-8")

        normalized_entries.append(
            NormalizationEntry(
                url=url,
                url_id=url_id,
                parsed_path=str(parsed_path),
                normalized_path=str(out_path),
                ok=True,
                original_chars=original_chars,
                normalized_chars=len(cleaned),
                removed_lines=removed_lines,
                removed_repeated_lines=removed_repeated_lines,
                flags=flags,
            )
        )

    report = {
        "generated_at": _utc_now_iso(),
        "source_parse_report": str(parse_report_path),
        "repeated_line_threshold_docs": repeated_threshold,
        "repeated_lines_count": len(repeated_lines),
        "counts": {
            "total": len(normalized_entries),
            "ok": sum(1 for x in normalized_entries if x.ok),
            "failed": sum(1 for x in normalized_entries if not x.ok),
        },
        "entries": [e.__dict__ for e in normalized_entries],
    }

    _write_json(OUTPUT_DIR / "normalization_report.json", report)
    print(json.dumps(report["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


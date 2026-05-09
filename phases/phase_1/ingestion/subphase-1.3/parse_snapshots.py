from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"
PARSED_DIR = OUTPUT_DIR / "parsed"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag in {"p", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in {"p", "li"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        txt = data.strip()
        if txt:
            self._chunks.append(txt + " ")

    def text(self) -> str:
        raw = "".join(self._chunks)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


@dataclass(frozen=True)
class ParseEntry:
    url: str
    url_id: str
    snapshot_path: str
    parsed_path: str | None
    ok: bool
    doc_type: str
    extracted_chars: int
    flags: list[str]
    error: str | None


def _detect_doc_type(url: str, content_type: str | None, snapshot_path: Path) -> str:
    path = urlparse(url).path.lower()
    if snapshot_path.suffix.lower() == ".pdf" or path.endswith(".pdf") or (content_type and "pdf" in content_type.lower()):
        return "pdf"
    if snapshot_path.suffix.lower() in {".html", ".htm"} or (content_type and "html" in content_type.lower()):
        return "html"
    return "unknown"


def _parse_html_bytes(raw: bytes) -> tuple[str, list[str]]:
    flags: list[str] = []
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = raw.decode("latin-1", errors="replace")
        flags.append("decoded_latin1_fallback")

    extractor = _HTMLTextExtractor()
    extractor.feed(text)
    out = extractor.text()
    if not out:
        flags.append("empty_extracted_text")
    return out, flags


def _parse_pdf_bytes(raw: bytes) -> tuple[str, list[str], str | None]:
    flags: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "", ["parser_missing_pypdf"], "pypdf_not_installed"

    try:
        import io

        reader = PdfReader(io.BytesIO(raw))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
        out = "\n\n".join(parts).strip()
        if not out:
            flags.append("empty_extracted_text")
            flags.append("ocr_may_be_needed")
        return out, flags, None
    except Exception as e:
        return "", ["pdf_parse_failed"], f"{type(e).__name__}: {e}"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_index_path = Path(__file__).resolve().parents[1] / "subphase-1.2" / "output" / "snapshot_index.json"
    idx = _read_json(snapshot_index_path)

    entries = idx.get("entries", [])

    report: dict[str, Any] = {
        "generated_at": _utc_now_iso(),
        "source_snapshot_index": str(snapshot_index_path),
        "counts": {"total": 0, "ok": 0, "failed": 0},
        "entries": [],
    }

    for e in entries:
        url = e["url"]
        url_id = e["url_id"]
        snapshot_path = Path(e["snapshot_path"])
        content_type = e.get("content_type")

        raw = snapshot_path.read_bytes()
        doc_type = _detect_doc_type(url, content_type, snapshot_path)

        parsed_text = ""
        flags: list[str] = []
        err: str | None = None
        ok = True

        if doc_type == "html":
            parsed_text, flags = _parse_html_bytes(raw)
        elif doc_type == "pdf":
            parsed_text, flags, err = _parse_pdf_bytes(raw)
            if err:
                ok = False
        else:
            ok = False
            err = "unknown_document_type"
            flags.append("unknown_document_type")

        parsed_path: Path | None = None
        if ok:
            parsed_path = PARSED_DIR / f"{url_id}.txt"
            parsed_path.write_text(parsed_text + "\n", encoding="utf-8")

        entry = ParseEntry(
            url=url,
            url_id=url_id,
            snapshot_path=str(snapshot_path),
            parsed_path=str(parsed_path) if parsed_path else None,
            ok=ok,
            doc_type=doc_type,
            extracted_chars=len(parsed_text),
            flags=flags,
            error=err,
        )

        report["entries"].append(entry.__dict__)

    report["counts"]["total"] = len(report["entries"])
    report["counts"]["ok"] = sum(1 for x in report["entries"] if x["ok"])
    report["counts"]["failed"] = report["counts"]["total"] - report["counts"]["ok"]

    (OUTPUT_DIR / "parse_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(json.dumps(report["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


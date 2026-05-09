from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"

PHASE0_DIR = Path(__file__).resolve().parents[3] / "phase_0"
SUBPHASE_1_2_DIR = Path(__file__).resolve().parents[1] / "subphase-1.2"
SUBPHASE_1_3_DIR = Path(__file__).resolve().parents[1] / "subphase-1.3"
SUBPHASE_1_4_DIR = Path(__file__).resolve().parents[1] / "subphase-1.4"


DEFAULT_TARGET_CHARS = 900
DEFAULT_OVERLAP_CHARS = 150
MIN_CHUNK_CHARS = 120


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _normalize_ws(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """
    Split by the normalization markers introduced in 1.4: lines like `## Exit Load`.
    Returns list of (section_title, section_text) where title may be 'root'.
    """
    t = _normalize_ws(text)
    if not t:
        return [("root", "")]

    lines = t.split("\n")
    sections: list[tuple[str, list[str]]] = []
    cur_title = "root"
    cur: list[str] = []

    header_re = re.compile(r"^\s*##\s+(?P<title>.+?)\s*$")
    for ln in lines:
        m = header_re.match(ln)
        if m:
            sections.append((cur_title, cur))
            cur_title = m.group("title").strip()
            cur = []
            continue
        cur.append(ln)
    sections.append((cur_title, cur))

    out: list[tuple[str, str]] = []
    for title, parts in sections:
        body = _normalize_ws("\n".join(parts))
        if body:
            out.append((title, body))
    if not out:
        return [("root", t)]
    return out


def _sentenceish_split(text: str) -> list[str]:
    # Heuristic split that works ok for flattened HTML: split on period/question/exclamation + space
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _paragraph_split(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    parts = [re.sub(r"\s+", " ", p).strip() for p in parts]
    return [p for p in parts if p]


def _chunk_text(text: str, target_chars: int, overlap_chars: int) -> list[tuple[str, int, int]]:
    """
    Create overlapping chunks, trying to end on sentence boundaries.
    Returns list of (chunk_text, start_char, end_char) offsets within `text`.
    """
    t = text.strip()
    if not t:
        return []

    if len(t) <= target_chars:
        return [(t, 0, len(t))]

    paragraphs = _paragraph_split(t)
    if len(paragraphs) <= 1:
        sentences = _sentenceish_split(t)
        # fallback raw slicing
        out: list[tuple[str, int, int]] = []
        start = 0
        while start < len(t):
            end = min(len(t), start + target_chars)
            out.append((t[start:end].strip(), start, end))
            if end == len(t):
                break
            start = max(0, end - overlap_chars)
        return out

    # Build chunks by adding paragraphs until target met
    out: list[tuple[str, int, int]] = []
    # Map paragraph -> its start offset by searching sequentially
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for p in paragraphs:
        i = t.find(p, cursor)
        if i < 0:
            i = cursor
        j = i + len(p)
        offsets.append((i, j))
        cursor = j

    i = 0
    while i < len(paragraphs):
        chunk_start = offsets[i][0]
        chunk_end = chunk_start
        j = i
        while j < len(paragraphs) and (offsets[j][1] - chunk_start) <= target_chars:
            chunk_end = offsets[j][1]
            j += 1
        if chunk_end == chunk_start:
            # single very long paragraph
            chunk_end = min(len(t), chunk_start + target_chars)
            j = i + 1

        chunk = t[chunk_start:chunk_end].strip()
        out.append((chunk, chunk_start, chunk_end))

        if chunk_end >= len(t):
            break

        # move i forward but keep overlap
        next_start = max(chunk_start, chunk_end - overlap_chars)
        # find first paragraph starting at/after next_start
        k = i
        while k < len(paragraphs) and offsets[k][0] < next_start:
            k += 1
        i = max(k, i + 1)

    # Merge tiny chunks forward where possible
    merged: list[tuple[str, int, int]] = []
    buf_text = ""
    buf_start = 0
    buf_end = 0
    for c_text, c_start, c_end in out:
        if not buf_text:
            buf_text, buf_start, buf_end = c_text, c_start, c_end
            continue
        if len(buf_text) < MIN_CHUNK_CHARS:
            buf_text = (buf_text + "\n\n" + c_text).strip()
            buf_end = c_end
            continue
        merged.append((buf_text, buf_start, buf_end))
        buf_text, buf_start, buf_end = c_text, c_start, c_end
    if buf_text:
        merged.append((buf_text, buf_start, buf_end))

    # Drop remaining ultra-small chunks if we have others
    if len(merged) > 1:
        merged = [m for m in merged if len(m[0]) >= max(20, MIN_CHUNK_CHARS // 3)]

    return merged


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    offsets: dict[str, int]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    normalization_report_path = SUBPHASE_1_4_DIR / "output" / "normalization_report.json"
    snapshot_index_path = SUBPHASE_1_2_DIR / "output" / "snapshot_index.json"
    parse_report_path = SUBPHASE_1_3_DIR / "output" / "parse_report.json"

    schemes_path = PHASE0_DIR / "corpus" / "schemes.json"
    manifest_path = PHASE0_DIR / "corpus" / "manifest.json"

    norm = _read_json(normalization_report_path)
    snap = _read_json(snapshot_index_path)
    parsed = _read_json(parse_report_path)
    schemes = _read_json(schemes_path)
    manifest = _read_json(manifest_path)

    # Build lookup maps
    url_to_scheme_id: dict[str, str] = {}
    for s in schemes.get("schemes", []):
        if not isinstance(s, dict):
            continue
        u = s.get("groww_url")
        sid = s.get("scheme_id")
        if isinstance(u, str) and isinstance(sid, str):
            url_to_scheme_id[u] = sid

    url_to_snapshot_meta: dict[str, dict[str, Any]] = {}
    for e in snap.get("entries", []):
        url_to_snapshot_meta[e["url"]] = e

    url_to_parse_meta: dict[str, dict[str, Any]] = {}
    for e in parsed.get("entries", []):
        url_to_parse_meta[e["url"]] = e

    chunks_out_path = OUTPUT_DIR / "chunks.jsonl"
    chunk_index_path = OUTPUT_DIR / "chunk_index.json"

    chunks: list[Chunk] = []
    chunk_index: dict[str, Any] = {
        "generated_at": _utc_now_iso(),
        "inputs": {
            "normalization_report": str(normalization_report_path),
            "snapshot_index": str(snapshot_index_path),
            "parse_report": str(parse_report_path),
            "schemes": str(schemes_path),
            "manifest": str(manifest_path),
        },
        "chunking": {
            "target_chars": DEFAULT_TARGET_CHARS,
            "overlap_chars": DEFAULT_OVERLAP_CHARS,
            "section_split_marker": "## <label>",
        },
        "documents": [],
        "chunks": {},
    }

    for doc in norm.get("entries", []):
        if not doc.get("ok"):
            continue

        url = doc["url"]
        url_id = doc["url_id"]
        normalized_path = Path(doc["normalized_path"])
        text = _read_text(normalized_path)
        text = _normalize_ws(text)

        snap_meta = url_to_snapshot_meta.get(url, {})
        parse_meta = url_to_parse_meta.get(url, {})

        fetched_at = snap_meta.get("fetched_at_utc")
        content_hash = snap_meta.get("content_hash_sha256")
        content_type = snap_meta.get("content_type")
        document_type = parse_meta.get("doc_type") or ("pdf" if (content_type and "pdf" in content_type.lower()) else "html")

        scheme_id = url_to_scheme_id.get(url)

        doc_record = {
            "url": url,
            "url_id": url_id,
            "scheme_id": scheme_id,
            "document_type": document_type,
            "fetched_at_utc": fetched_at,
            "content_hash_sha256": content_hash,
            "normalized_path": str(normalized_path),
            "normalized_chars": len(text),
        }
        chunk_index["documents"].append(doc_record)

        sections = _split_into_sections(text)
        seq = 0
        for section_title, section_text in sections:
            pieces = _chunk_text(section_text, DEFAULT_TARGET_CHARS, DEFAULT_OVERLAP_CHARS)
            for piece_text, start_char, end_char in pieces:
                if not piece_text.strip():
                    continue
                # Drop tiny fragments that are almost always UI residue in this corpus.
                if len(piece_text.strip()) < 40:
                    continue

                chunk_id = f"{url_id}_{seq:04d}"
                seq += 1

                meta = {
                    "source_url": url,
                    "url_id": url_id,
                    "scheme_id": scheme_id,
                    "document_type": document_type,
                    "section": section_title,
                    "fetched_at_utc": fetched_at,
                    "content_hash_sha256": content_hash,
                    "project": manifest.get("project", {}).get("name"),
                }

                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        text=piece_text,
                        metadata=meta,
                        offsets={"start_char": int(start_char), "end_char": int(end_char)},
                    )
                )

                chunk_index["chunks"][chunk_id] = {
                    "source_url": url,
                    "scheme_id": scheme_id,
                    "document_type": document_type,
                    "section": section_title,
                    "start_char": int(start_char),
                    "end_char": int(end_char),
                    "fetched_at_utc": fetched_at,
                    "content_hash_sha256": content_hash,
                }

    with chunks_out_path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({"chunk_id": c.chunk_id, "text": c.text, "metadata": c.metadata, "offsets": c.offsets}, ensure_ascii=False) + "\n")

    _write_json(chunk_index_path, chunk_index)

    print(json.dumps({"documents": len(chunk_index["documents"]), "chunks": len(chunks)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


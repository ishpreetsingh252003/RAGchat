from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal


ROOT = Path(__file__).resolve().parents[3]

CHUNKS_JSONL = ROOT / "phases" / "phase_1" / "ingestion" / "subphase-1.5" / "output" / "chunks.jsonl"
CHUNK_INDEX_JSON = ROOT / "phases" / "phase_1" / "ingestion" / "subphase-1.5" / "output" / "chunk_index.json"
SCHEMES_JSON = ROOT / "phases" / "phase_0" / "corpus" / "schemes.json"


SECTION_KEYWORDS: dict[str, list[str]] = {
    "Expense Ratio": ["expense ratio", "expense", "ter", "total expense"],
    "Exit Load": ["exit load", "redeem", "redemption", "load"],
    "Minimum SIP": ["minimum sip", "min sip", "sip amount", "sip minimum"],
    "Minimum Lump Sum": ["minimum investment", "min investment", "lumpsum", "lump sum", "minimum lumpsum"],
    "Benchmark": ["benchmark", "index", "nifty", "bse"],
    "Risk": ["risk", "riskometer", "very high", "moderate", "low risk"],
    "Lock-in": ["lock-in", "lock in", "lockin"],
    "ELSS": ["elss", "tax saver", "80c"],
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _detect_section(query: str) -> str | None:
    q = query.lower()
    for section, keys in SECTION_KEYWORDS.items():
        if any(k in q for k in keys):
            return section
    return None


def _build_alias_index(schemes: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for s in schemes.get("schemes", []):
        if not isinstance(s, dict):
            continue
        sid = s.get("scheme_id")
        if not isinstance(sid, str):
            continue
        aliases = s.get("aliases", [])
        if isinstance(aliases, list):
            for a in aliases:
                if isinstance(a, str) and a.strip():
                    out.append((a.lower(), sid))
        # also match display name tokens
        dn = s.get("display_name")
        if isinstance(dn, str) and dn.strip():
            out.append((dn.lower(), sid))
    # sort longer aliases first so "hdfc large cap fund" beats "hdfc large cap"
    out.sort(key=lambda x: len(x[0]), reverse=True)
    return out


def _detect_scheme_id(query: str, alias_index: list[tuple[str, str]]) -> str | None:
    q = query.lower()
    for alias, sid in alias_index:
        if alias in q:
            return sid
    return None


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.2, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs = docs
        self.N = len(docs)
        self.doc_lens = [len(d) for d in docs]
        self.avgdl = (sum(self.doc_lens) / self.N) if self.N else 0.0

        df: dict[str, int] = {}
        for d in docs:
            seen = set(d)
            for t in seen:
                df[t] = df.get(t, 0) + 1
        self.df = df

    def idf(self, term: str) -> float:
        n = self.df.get(term, 0)
        # standard BM25 IDF
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5)) if self.N else 0.0

    def score(self, query_terms: list[str], doc_terms: list[str]) -> float:
        if not doc_terms:
            return 0.0
        tf: dict[str, int] = {}
        for t in doc_terms:
            tf[t] = tf.get(t, 0) + 1

        dl = len(doc_terms)
        score = 0.0
        for term in query_terms:
            if term not in tf:
                continue
            idf = self.idf(term)
            freq = tf[term]
            denom = freq + self.k1 * (1 - self.b + self.b * (dl / (self.avgdl or 1.0)))
            score += idf * (freq * (self.k1 + 1)) / denom
        return score


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]


def retrieve(query: str, k: int = 5) -> dict[str, Any]:
    schemes = _read_json(SCHEMES_JSON)
    alias_index = _build_alias_index(schemes)

    scheme_id = _detect_scheme_id(query, alias_index)
    section = _detect_section(query)

    all_chunks = list(_iter_jsonl(CHUNKS_JSONL))

    def passes_filters(c: dict[str, Any], mode: Literal["scheme+section", "scheme", "section", "none"]) -> bool:
        meta = c.get("metadata", {})
        if not isinstance(meta, dict):
            return False
        if mode == "scheme+section":
            return meta.get("scheme_id") == scheme_id and (section is None or meta.get("section") == section)
        if mode == "scheme":
            return meta.get("scheme_id") == scheme_id
        if mode == "section":
            return section is not None and meta.get("section") == section
        return True

    # Progressive fallback
    modes: list[Literal["scheme+section", "scheme", "section", "none"]] = []
    if scheme_id and section:
        modes = ["scheme+section", "scheme", "section", "none"]
    elif scheme_id:
        modes = ["scheme", "none"]
    elif section:
        modes = ["section", "none"]
    else:
        modes = ["none"]

    candidates: list[dict[str, Any]] = []
    used_mode: str = "none"
    for m in modes:
        filtered = [c for c in all_chunks if passes_filters(c, m)]
        if filtered:
            candidates = filtered
            used_mode = m
            break

    q_terms = _tokenize(query)
    docs_terms = [_tokenize(c.get("text", "") or "") for c in candidates]
    bm25 = BM25(docs_terms)

    scored: list[RetrievalResult] = []
    for c, terms in zip(candidates, docs_terms):
        score = bm25.score(q_terms, terms)
        meta = c.get("metadata", {})
        if not isinstance(meta, dict):
            meta = {}
        scored.append(
            RetrievalResult(
                chunk_id=c["chunk_id"],
                score=score,
                text=c.get("text", "") or "",
                metadata=meta,
            )
        )

    # Rerank: prefer higher score; tie-break by fetched_at_utc if present
    def tie_key(r: RetrievalResult) -> tuple[float, str]:
        fa = r.metadata.get("fetched_at_utc") or ""
        return (r.score, str(fa))

    scored.sort(key=tie_key, reverse=True)

    # Dedup by (source_url, section) to increase diversity
    seen: set[tuple[str, str]] = set()
    top: list[RetrievalResult] = []
    for r in scored:
        src = str(r.metadata.get("source_url") or "")
        sec = str(r.metadata.get("section") or "")
        key = (src, sec)
        if key in seen:
            continue
        seen.add(key)
        top.append(r)
        if len(top) >= k:
            break

    citation_url = None
    if top:
        citation_url = top[0].metadata.get("source_url")

    return {
        "query": query,
        "detected": {"scheme_id": scheme_id, "section": section, "filter_mode": used_mode},
        "citation_url_candidate": citation_url,
        "results": [
            {"chunk_id": r.chunk_id, "score": r.score, "metadata": r.metadata, "text": r.text}
            for r in top
        ],
    }


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser()
    ap.add_argument("query", type=str)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()
    out = retrieve(args.query, k=args.k)
    # Windows terminals can default to cp1252; emit UTF-8 bytes directly.
    payload = (json.dumps(out, indent=2, ensure_ascii=False) + "\n").encode("utf-8", errors="replace")
    sys.stdout.buffer.write(payload)


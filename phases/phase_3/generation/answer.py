from __future__ import annotations

import warnings
# Suppress FutureWarning for deprecated google.generativeai package
warnings.filterwarnings('ignore', category=FutureWarning)

import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


ROOT = Path(__file__).resolve().parents[3]

# Load Phase 2 retriever without package layout
_RETRIEVER_PATH = ROOT / "phases" / "phase_2" / "retrieval" / "retriever.py"
_SPEC = importlib.util.spec_from_file_location("phase2_retriever", _RETRIEVER_PATH)
_retriever = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
# Required so dataclass processing can resolve the module namespace
sys.modules[_SPEC.name] = _retriever
_SPEC.loader.exec_module(_retriever)  # type: ignore[union-attr]
retrieve = _retriever.retrieve

INDEX_MANIFEST = ROOT / "phases" / "phase_1" / "ingestion" / "subphase-1.7" / "output" / "index_build_manifest.json"

MAX_SENTENCES = 3
MIN_BM25_SCORE = 0.0
RETRIEVAL_K = 5

# Do not encourage or process PII in queries
_PII_PATTERNS = [
    (re.compile(r"\b\d{10}\b"), "phone-like"),
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I), "pan-like"),
    (re.compile(r"\b\d{12}\b"), "aadhaar-like"),
    (re.compile(r"\S+@\S+\.\S+"), "email-like"),
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _detect_pii_reason(query: str) -> str | None:
    q = query.strip()
    for rx, label in _PII_PATTERNS:
        if rx.search(q):
            return label
    return None


def _split_sentences(text: str, max_n: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(p)
        if len(out) >= max_n:
            break
    if not out and text:
        out = [text[:500] + ("…" if len(text) > 500 else "")]
    return out


def _footer_date_from_chunks(chunks_meta: list[dict[str, Any]]) -> str | None:
    dates: list[str] = []
    for m in chunks_meta:
        fa = m.get("fetched_at_utc")
        if isinstance(fa, str) and fa:
            dates.append(fa)
    if not dates:
        return None
    mx = max(dates)
    # ISO date for footer
    if "T" in mx:
        return mx.split("T")[0]
    return mx[:10] if len(mx) >= 10 else mx


def _footer_date_fallback() -> str | None:
    p = INDEX_MANIFEST
    if not p.is_file():
        return None
    try:
        m = _read_json(p)
        return m.get("freshness", {}).get("footer_date_suggestion")
    except Exception:
        return None


# Global client instance
_client: Groq | None = None

def _get_client() -> Groq:
    """Get or initialize the Groq client."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        _client = Groq(api_key=api_key)
    return _client

def _init_gemini() -> None:
    """Ensures Groq client is initialized (renamed internally but kept for compatibility)."""
    _get_client()


def _synthesize_with_groq(query: str, context: str, citation_url: str, is_general_topic: bool = False) -> list[str]:
    """
    Use Groq to synthesize an answer from retrieved context.
    Enforces facts-only, 3-sentence limit, and citation accuracy.
    """
    client = _get_client()
    
    if is_general_topic:
        # General topic - provide educational/generic answer
        prompt = f"""You are a helpful and friendly mutual fund chatbot. Your goal is to explain facts about mutual funds simply so that even a beginner can understand.

Context (from educational sources):
{context}

User Question: {query}

Rules for your response:
1. Answer using ONLY the information in the provided context.
2. Provide a GENERAL educational answer about the topic (e.g., "An expense ratio is...").
3. Do NOT mention any specific fund names, scheme names, or fund-specific details.
4. Maximum 3 sentences.
5. Use simple language and avoid complex jargon. If you must use a technical term, explain it briefly.
6. Facts only - never give investment advice or say if a fund is "good" or "bad".
7. If the context doesn't have the answer, provide a general explanation based on your knowledge.

Answer:"""
    else:
        # Fund-specific question
        prompt = f"""You are a helpful and friendly mutual fund chatbot. Your goal is to explain facts about mutual funds simply so that even a beginner can understand.

Context:
{context}

User Question: {query}

Rules for your response:
1. Answer using ONLY the information in the provided context.
2. Be conversational but professional (e.g., "The exit load for this fund is...").
3. Maximum 3 sentences.
4. Use simple language and avoid complex jargon. If you must use a technical term, explain it briefly.
5. Facts only - never give investment advice or say if a fund is "good" or "bad".
6. If the context doesn't have the answer, politely let the user know.

Answer:"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            max_tokens=256,
        )
        answer_text = chat_completion.choices[0].message.content.strip()
        
        # Split into sentences and limit to 3
        sentences = _split_sentences(answer_text, MAX_SENTENCES)
        return sentences[:MAX_SENTENCES]
    except Exception as e:
        # Fallback to simple text extraction if Groq fails
        return _split_sentences(context, MAX_SENTENCES)[:MAX_SENTENCES]


def synthesize(query: str, k: int = RETRIEVAL_K) -> dict[str, Any]:
    pii = _detect_pii_reason(query)
    if pii:
        return {
            "grounded": False,
            "reason": "pii_in_query",
            "answer_sentences": [
                "This assistant does not process or store personal identifiers (for example PAN, Aadhaar, phone numbers, or email).",
                "Please remove any personal information from your question and ask again using only general, factual wording.",
            ],
            "citation_url": None,
            "footer": None,
            "retrieval": None,
        }

    ret = retrieve(query, k=k)
    results = ret.get("results") or []
    if not results:
        return {
            "grounded": False,
            "reason": "no_retrieval_results",
            "answer_sentences": [
                "I do not find enough information in the curated sources to answer this question.",
                "Try rephrasing with a specific scheme name and fact (for example exit load, minimum SIP, or benchmark).",
            ],
            "citation_url": None,
            "footer": None,
            "retrieval": ret,
        }

    top = results[0]
    score = float(top.get("score", 0.0))
    text = (top.get("text") or "").strip()
    meta = top.get("metadata") or {}
    detected = ret.get("detected") or {}
    filter_mode = detected.get("filter_mode")
    scheme_detected = detected.get("scheme_id")

    # Allow general topic questions if section is detected, only refuse if no scheme AND no section
    section_detected = detected.get("section")
    if filter_mode == "none" and scheme_detected is None and section_detected is None:
        return {
            "grounded": False,
            "reason": "no_entity_or_topic_anchor",
            "answer_sentences": [
                "I cannot answer this from the in-scope fund sources without a clearer question.",
                "Ask about a specific topic like expense ratio, exit load, SIP, or ELSS, or include a fund name for detailed information.",
            ],
            "citation_url": None,
            "footer": None,
            "retrieval": ret,
        }

    if score < MIN_BM25_SCORE or len(text) < 30:
        return {
            "grounded": False,
            "reason": "insufficient_evidence",
            "answer_sentences": [
                "Based on the curated sources available, I cannot confidently answer this question.",
                "No citation is provided because the retrieved text does not clearly support a specific factual answer.",
            ],
            "citation_url": None,
            "footer": None,
            "retrieval": ret,
        }

    # Initialize Groq for answer synthesis
    _init_gemini()
    
    # For general topic questions (no specific scheme), use educational context
    is_general_topic = scheme_detected is None and section_detected is not None
    
    # Use Groq to synthesize answer from context
    sentences = _synthesize_with_groq(query, text, meta.get("source_url", ""), is_general_topic)
    
    # For general topics, use educational citation instead of fund-specific URL
    if is_general_topic:
        citation = "https://www.amfiindia.com/investor-corner/knowledge-center/introduction-to-mutual-funds.html"
    else:
        citation = meta.get("source_url")
    if not citation or not isinstance(citation, str):
        return {
            "grounded": False,
            "reason": "missing_source_url",
            "answer_sentences": sentences[:MAX_SENTENCES]
            or ["The retrieved excerpt does not include a usable source URL for citation."],
            "citation_url": None,
            "footer": None,
            "retrieval": ret,
        }

    # Footer from chunks used (top result + siblings for max freshness)
    metas = [r.get("metadata") or {} for r in results[:3]]
    d = _footer_date_from_chunks(metas) or _footer_date_fallback()
    footer = f"Last updated from sources: {d}" if d else None

    return {
        "grounded": True,
        "reason": "ok",
        "answer_sentences": sentences[:MAX_SENTENCES],
        "citation_url": citation.strip(),
        "footer": footer,
        "retrieval": {
            "detected": ret.get("detected"),
            "top_score": score,
            "chunk_id": top.get("chunk_id"),
        },
    }


def render_plain(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for s in payload.get("answer_sentences") or []:
        parts.append(s.strip())
    body = " ".join(parts)
    lines = [body]
    url = payload.get("citation_url")
    if url:
        lines.append(f"Source: {url}")
    foot = payload.get("footer")
    if foot:
        lines.append(foot)
    return "\n".join(lines)


def main() -> int:
    ap_argv = sys.argv[1:]
    if not ap_argv:
        sys.stderr.buffer.write(b"usage: answer.py \"<query>\"\n")
        return 2
    query = ap_argv[0]
    payload = synthesize(query)
    out = {"structured": payload, "plain_text": render_plain(payload)}
    data = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    sys.stdout.buffer.write(data.encode("utf-8", errors="replace"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import json
import os
import re
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Suppress FutureWarning for deprecated google.generativeai package
warnings.filterwarnings('ignore', category=FutureWarning)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

import google.genai as genai


HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"
EMBED_DIR = OUTPUT_DIR / "embeddings"


DEFAULT_DIM = 3072  # Gemini embedding dimensions (models/gemini-embedding-001)
DEFAULT_EMBEDDER_ID = "gemini-embedding-001"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _init_gemini() -> None:
    """Initialize Gemini API with API key from environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    import google.generativeai as genai_legacy
    genai_legacy.configure(api_key=api_key)


def _gemini_embed(text: str) -> list[float]:
    """
    Generate embeddings using Google's Gemini embedding model.
    Provides semantic understanding for better retrieval.
    """
    import google.generativeai as genai_legacy
    model = "models/gemini-embedding-001"
    result = genai_legacy.embed_content(
        model=model,
        content=text,
        task_type="retrieval_document"
    )
    return result["embedding"]


@dataclass(frozen=True)
class EmbedRecord:
    chunk_id: str
    vector: list[float]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EMBED_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize Gemini API
    _init_gemini()

    chunks_path = Path(__file__).resolve().parents[1] / "subphase-1.5" / "output" / "chunks.jsonl"
    embeddings_path = EMBED_DIR / "embeddings.jsonl"
    manifest_path = OUTPUT_DIR / "embed_manifest.json"

    dim = DEFAULT_DIM
    embedder_id = DEFAULT_EMBEDDER_ID

    count = 0
    empty = 0

    with chunks_path.open("r", encoding="utf-8") as fin, embeddings_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            chunk_id = obj["chunk_id"]
            text = obj.get("text", "") or ""
            if not text.strip():
                empty += 1
                # Create zero vector for empty chunks to maintain consistency
                vec = [0.0] * dim
            else:
                # Use Gemini embeddings for semantic understanding
                vec = _gemini_embed(text)
            rec = {"chunk_id": chunk_id, "vector": vec}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    embed_manifest: dict[str, Any] = {
        "generated_at": _utc_now_iso(),
        "embedder": {
            "id": embedder_id,
            "type": "gemini_embedding",
            "dimensions": dim,
            "model": "models/embedding-001",
            "notes": "Google Gemini embedding model for semantic understanding and improved retrieval quality.",
        },
        "inputs": {
            "chunks_jsonl": str(chunks_path),
        },
        "counts": {
            "chunks": count,
            "empty_text_chunks": empty,
        },
        "outputs": {
            "embeddings_jsonl": str(embeddings_path),
        },
    }

    manifest_path.write_text(json.dumps(embed_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"chunks_embedded": count, "dimensions": dim}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


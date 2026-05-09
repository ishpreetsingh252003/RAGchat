from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"

SUBPHASE_1_5_DIR = Path(__file__).resolve().parents[1] / "subphase-1.5"
SUBPHASE_1_6_DIR = Path(__file__).resolve().parents[1] / "subphase-1.6"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _max_fetched_at_utc(documents: list[dict[str, Any]]) -> str | None:
    vals = []
    for d in documents:
        v = d.get("fetched_at_utc")
        if isinstance(v, str) and v:
            vals.append(v)
    if not vals:
        return None
    return max(vals)


def _chroma_upsert(
    persist_dir: Path,
    collection_name: str,
    embeddings: dict[str, list[float]],
    metadatas: dict[str, dict[str, Any]],
) -> str:
    """
    Upsert into ChromaDB (required dependency).
    Returns success message.
    """
    import chromadb  # type: ignore

    client = chromadb.PersistentClient(path=str(persist_dir))
    col = client.get_or_create_collection(name=collection_name)

    ids = list(embeddings.keys())
    vectors = [embeddings[i] for i in ids]
    metas = [metadatas.get(i, {}) for i in ids]

    # Chunk uploads to avoid huge payloads
    batch = 256
    for start in range(0, len(ids), batch):
        sl = slice(start, start + batch)
        col.upsert(ids=ids[sl], embeddings=vectors[sl], metadatas=metas[sl])

    return f"chroma_upsert_ok(count={len(ids)})"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    chunk_index_path = SUBPHASE_1_5_DIR / "output" / "chunk_index.json"
    embeddings_path = SUBPHASE_1_6_DIR / "output" / "embeddings" / "embeddings.jsonl"
    embed_manifest_path = SUBPHASE_1_6_DIR / "output" / "embed_manifest.json"

    chunk_index = _read_json(chunk_index_path)
    embed_manifest = _read_json(embed_manifest_path)

    index_version = "index_v1"
    index_dir = OUTPUT_DIR / index_version
    index_dir.mkdir(parents=True, exist_ok=True)

    # Load embeddings into memory (small corpus for MVP)
    embeddings: dict[str, list[float]] = {}
    for obj in _iter_jsonl(embeddings_path):
        embeddings[obj["chunk_id"]] = obj["vector"]

    # Build metadata per chunk from chunk_index
    metadatas: dict[str, dict[str, Any]] = {}
    for chunk_id, meta in chunk_index.get("chunks", {}).items():
        if not isinstance(meta, dict):
            continue
        metadatas[chunk_id] = meta

    documents = chunk_index.get("documents", [])
    max_fetched_at = _max_fetched_at_utc(documents) or None

    # Use ChromaDB exclusively
    chroma_dir = index_dir / "chroma"
    chroma_msg = _chroma_upsert(
        persist_dir=chroma_dir,
        collection_name="mutual_fund_faq_chunks",
        embeddings=embeddings,
        metadatas=metadatas,
    )

    build_manifest = {
        "generated_at": _utc_now_iso(),
        "index_version": index_version,
        "index_dir": str(index_dir),
        "embedder": embed_manifest.get("embedder", {}),
        "counts": {
            "chunks": len(embeddings),
            "documents": len(documents) if isinstance(documents, list) else None,
        },
        "freshness": {
            "max_fetched_at_utc": max_fetched_at,
            "footer_date_suggestion": (max_fetched_at.split("T")[0] if isinstance(max_fetched_at, str) and "T" in max_fetched_at else None),
        },
        "inputs": {
            "chunk_index": str(chunk_index_path),
            "embeddings_jsonl": str(embeddings_path),
            "embed_manifest": str(embed_manifest_path),
        },
        "storage": {
            "chroma": {
                "persist_dir": str(chroma_dir),
                "message": chroma_msg,
                "collection": "mutual_fund_faq_chunks",
            },
        },
    }

    _write_json(OUTPUT_DIR / "index_build_manifest.json", build_manifest)

    print(json.dumps({"index_version": index_version, "chunks": len(embeddings), "storage": "chroma_only", "chroma": build_manifest["storage"]["chroma"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


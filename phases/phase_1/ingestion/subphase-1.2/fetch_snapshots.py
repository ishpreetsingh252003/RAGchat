from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"
SNAPSHOTS_DIR = OUTPUT_DIR / "snapshots"
PHASE0_DIR = Path(__file__).resolve().parents[3] / "phase_0"


DEFAULT_TIMEOUT_S = 30
DEFAULT_SLEEP_BETWEEN_REQUESTS_S = 0.25
USER_AGENT = "RAG-Chatbot/phase-1.2 (+facts-only; educational project)"


@dataclass(frozen=True)
class FetchResult:
    url: str
    ok: bool
    status_code: int | None
    fetched_at_utc: str
    content_type: str | None
    content_length: int | None
    content_hash_sha256: str | None
    snapshot_path: str | None
    error: str | None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_url_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]


def _guess_extension(url: str, content_type: str | None) -> str:
    path = urlparse(url).path.lower()
    if path.endswith(".pdf") or (content_type and "pdf" in content_type.lower()):
        return ".pdf"
    if content_type and "html" in content_type.lower():
        return ".html"
    if path.endswith(".htm") or path.endswith(".html"):
        return ".html"
    return ".bin"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    validated_urls_path = Path(__file__).resolve().parents[1] / "subphase-1.1" / "output" / "validated_urls.json"
    whitelist_path = PHASE0_DIR / "corpus" / "whitelist.json"

    validated = _read_json(validated_urls_path)
    whitelist = _read_json(whitelist_path)

    allowed_prefixes: list[str] = whitelist.get("allowed_url_prefixes", [])

    urls: list[str] = list(validated.get("urls", []))

    fetch_log_path = OUTPUT_DIR / "fetch_log.jsonl"
    snapshot_index_path = OUTPUT_DIR / "snapshot_index.json"

    index: dict[str, Any] = {
        "generated_at": _utc_now_iso(),
        "source_validated_urls": str(validated_urls_path),
        "entries": [],
    }

    results: list[FetchResult] = []
    for url in urls:
        fetched_at = _utc_now_iso()

        # Defensive: re-check allowed prefixes before any fetch
        if not any(url.startswith(p) for p in allowed_prefixes):
            res = FetchResult(
                url=url,
                ok=False,
                status_code=None,
                fetched_at_utc=fetched_at,
                content_type=None,
                content_length=None,
                content_hash_sha256=None,
                snapshot_path=None,
                error="url_prefix_not_allowed",
            )
            results.append(res)
            continue

        req = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8",
            },
            method="GET",
        )

        try:
            with urlopen(req, timeout=DEFAULT_TIMEOUT_S) as resp:
                status = getattr(resp, "status", None)
                headers = getattr(resp, "headers", None)
                content_type = headers.get("Content-Type") if headers else None
                raw = resp.read()

            content_hash = _sha256_bytes(raw)
            ext = _guess_extension(url, content_type)
            url_id = _stable_url_id(url)
            snapshot_name = f"{url_id}{ext}"
            snapshot_path = SNAPSHOTS_DIR / snapshot_name
            snapshot_path.write_bytes(raw)

            res = FetchResult(
                url=url,
                ok=True,
                status_code=int(status) if status is not None else 200,
                fetched_at_utc=fetched_at,
                content_type=content_type,
                content_length=len(raw),
                content_hash_sha256=content_hash,
                snapshot_path=str(snapshot_path),
                error=None,
            )
            results.append(res)

            index["entries"].append(
                {
                    "url": url,
                    "url_id": url_id,
                    "snapshot_path": str(snapshot_path),
                    "snapshot_bytes": len(raw),
                    "content_type": content_type,
                    "content_hash_sha256": content_hash,
                    "fetched_at_utc": fetched_at,
                    "status_code": res.status_code,
                }
            )

        except HTTPError as e:
            results.append(
                FetchResult(
                    url=url,
                    ok=False,
                    status_code=int(getattr(e, "code", 0)) or None,
                    fetched_at_utc=fetched_at,
                    content_type=None,
                    content_length=None,
                    content_hash_sha256=None,
                    snapshot_path=None,
                    error=f"HTTPError: {e}",
                )
            )
        except URLError as e:
            results.append(
                FetchResult(
                    url=url,
                    ok=False,
                    status_code=None,
                    fetched_at_utc=fetched_at,
                    content_type=None,
                    content_length=None,
                    content_hash_sha256=None,
                    snapshot_path=None,
                    error=f"URLError: {e}",
                )
            )
        except Exception as e:
            results.append(
                FetchResult(
                    url=url,
                    ok=False,
                    status_code=None,
                    fetched_at_utc=fetched_at,
                    content_type=None,
                    content_length=None,
                    content_hash_sha256=None,
                    snapshot_path=None,
                    error=f"Exception: {type(e).__name__}: {e}",
                )
            )

        time.sleep(DEFAULT_SLEEP_BETWEEN_REQUESTS_S)

    # Write log + index
    with fetch_log_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r.__dict__, ensure_ascii=False) + "\n")

    snapshot_index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Console summary
    ok_count = sum(1 for r in results if r.ok)
    fail_count = len(results) - ok_count
    print(json.dumps({"fetched_ok": ok_count, "failed": fail_count, "total": len(results)}, indent=2))

    return 0 if fail_count == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())


from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


PHASE0_DIR = Path(__file__).resolve().parents[3] / "phase_0"
PHASE1_1_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PHASE1_1_DIR / "output"


TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "ref",
    "referrer",
}


@dataclass(frozen=True)
class Rejection:
    url: str
    reason: str
    detail: str | None = None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_https(url: str) -> bool:
    try:
        return urlparse(url).scheme.lower() == "https"
    except Exception:
        return False


def _canonicalize_url(url: str) -> str:
    """
    Normalize a URL for deduping and for whitelist matching.

    - Force https scheme as-is (we reject non-https elsewhere)
    - Lowercase scheme + hostname
    - Remove fragment
    - Remove common tracking query params
    - Trim trailing slash (except root)
    """
    p = urlparse(url)
    scheme = p.scheme.lower()
    netloc = p.netloc.lower()
    path = p.path or "/"

    # Remove fragment
    fragment = ""

    # Filter query params
    query_pairs = [(k, v) for (k, v) in parse_qsl(p.query, keep_blank_values=True)]
    filtered_pairs = [(k, v) for (k, v) in query_pairs if k.lower() not in TRACKING_QUERY_KEYS]
    query = urlencode(filtered_pairs, doseq=True)

    # Trim trailing slash (except root)
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunparse((scheme, netloc, path, p.params, query, fragment))


def _host(url: str) -> str:
    return urlparse(url).netloc.lower()


def _matches_any_prefix(url: str, allowed_prefixes: Iterable[str]) -> bool:
    u = url
    for prefix in allowed_prefixes:
        if u.startswith(prefix):
            return True
    return False


def _is_reasonable_url(url: str) -> tuple[bool, str]:
    if not url or not isinstance(url, str):
        return False, "empty_or_non_string"
    if not re.match(r"^https?://", url.strip(), flags=re.IGNORECASE):
        return False, "not_an_http_url"
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "parse_error"
    if not parsed.netloc:
        return False, "missing_host"
    if not parsed.path:
        return False, "missing_path"
    return True, "ok"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest_path = PHASE0_DIR / "corpus" / "manifest.json"
    whitelist_path = PHASE0_DIR / "corpus" / "whitelist.json"
    schemes_path = PHASE0_DIR / "corpus" / "schemes.json"

    manifest = _read_json(manifest_path)
    whitelist = _read_json(whitelist_path)
    schemes = _read_json(schemes_path)

    allowed_hosts = {h.lower() for h in whitelist.get("hosts", [])}
    allowed_prefixes = [p for p in whitelist.get("allowed_url_prefixes", [])]
    allowed_prefixes = [p.replace("HTTP://", "https://").replace("http://", "https://") for p in allowed_prefixes]

    # Collect candidate URLs
    anchor_urls = list(manifest.get("corpus", {}).get("anchor_urls", []))

    backlog_urls: list[str] = []
    for entry in manifest.get("corpus", {}).get("backlog_official_urls_to_add", []):
        if isinstance(entry, dict) and "url" in entry and isinstance(entry["url"], str):
            backlog_urls.append(entry["url"])

    scheme_urls = [s.get("groww_url") for s in schemes.get("schemes", []) if isinstance(s, dict)]
    scheme_urls = [u for u in scheme_urls if isinstance(u, str)]

    candidates_raw: list[dict[str, Any]] = []
    for u in anchor_urls:
        candidates_raw.append({"url": u, "source": "manifest.anchor_urls"})
    for u in backlog_urls:
        candidates_raw.append({"url": u, "source": "manifest.backlog_official_urls_to_add"})
    for u in scheme_urls:
        candidates_raw.append({"url": u, "source": "schemes.groww_url"})

    # Validate + normalize
    rejections: list[Rejection] = []
    accepted: dict[str, dict[str, Any]] = {}  # canonical_url -> details

    for item in candidates_raw:
        url = item["url"]
        ok, why = _is_reasonable_url(url)
        if not ok:
            rejections.append(Rejection(url=url, reason=why, detail=item["source"]))
            continue

        canonical = _canonicalize_url(url.strip())

        if not _is_https(canonical):
            rejections.append(Rejection(url=url, reason="non_https", detail=item["source"]))
            continue

        h = _host(canonical)
        if h not in allowed_hosts:
            rejections.append(Rejection(url=url, reason="host_not_whitelisted", detail=h))
            continue

        if not _matches_any_prefix(canonical, allowed_prefixes):
            rejections.append(Rejection(url=url, reason="prefix_not_allowed", detail=item["source"]))
            continue

        # Deduplicate by canonical URL while preserving provenance
        if canonical not in accepted:
            accepted[canonical] = {
                "url": canonical,
                "sources": [item["source"]],
                "host": h,
            }
        else:
            accepted[canonical]["sources"].append(item["source"])

    # Sanity: ensure manifest anchor_urls == scheme groww URLs set (canonicalized)
    anchor_set = {_canonicalize_url(u) for u in anchor_urls if isinstance(u, str)}
    scheme_set = {_canonicalize_url(u) for u in scheme_urls if isinstance(u, str)}
    anchor_minus_scheme = sorted(anchor_set - scheme_set)
    scheme_minus_anchor = sorted(scheme_set - anchor_set)

    summary = {
        "generated_at": date.today().isoformat(),
        "inputs": {
            "manifest": str(manifest_path.relative_to(PHASE0_DIR.parent)),
            "schemes": str(schemes_path.relative_to(PHASE0_DIR.parent)),
            "whitelist": str(whitelist_path.relative_to(PHASE0_DIR.parent)),
        },
        "counts": {
            "candidates_total": len(candidates_raw),
            "accepted_unique": len(accepted),
            "rejected": len(rejections),
        },
        "scope_checks": {
            "anchor_urls_not_in_schemes": anchor_minus_scheme,
            "scheme_urls_not_in_anchor_urls": scheme_minus_anchor,
            "note": "In Phase 0, anchors and scheme groww URLs should typically match 1:1.",
        },
    }

    validated_urls = sorted(accepted.keys())
    validated_payload = {
        "summary": summary,
        "urls": validated_urls,
        "details": [accepted[u] for u in validated_urls],
    }

    rejection_payload = {
        "summary": summary,
        "rejections": [r.__dict__ for r in rejections],
    }

    (OUTPUT_DIR / "validated_urls.json").write_text(
        json.dumps(validated_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUTPUT_DIR / "rejected_urls.json").write_text(
        json.dumps(rejection_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Friendly console output
    print(json.dumps(summary, indent=2))
    if anchor_minus_scheme or scheme_minus_anchor:
        print("\nWARNING: Phase 0 anchor URLs and scheme URLs differ; see scope_checks in output JSON.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


"""
Observability ringan untuk demo: payload API + log JSON satu-baris (opsional).

Aktifkan lewat environment — tidak mengubah perilaku pipeline tanpa flag tersebut.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from cag.cache import CACHE_THRESHOLD, QA_CACHE, cache_aktif


def observability_demo_enabled() -> bool:
    v = os.getenv("OBSERVABILITY_DEMO", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def structured_log_enabled() -> bool:
    v = os.getenv("STRUCTURED_LOG_JSON", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def observability_or_logging_enabled() -> bool:
    return observability_demo_enabled() or structured_log_enabled()


def _preview_chars() -> int:
    try:
        return max(80, int(os.getenv("OBSERVABILITY_PREVIEW_CHARS", "320")))
    except ValueError:
        return 320


def build_demo_observability(result: dict, elapsed_ms: float) -> Dict[str, Any]:
    """Snapshot aman untuk dashboard/demo: cuplikan teks + metrik, tanpa menyalin secret."""
    preview = _preview_chars()
    rd = result.get("retrieved_docs") or ""
    uc = result.get("user_context") or ""
    ni = result.get("normalized_issue") or ""

    return {
        "latency_ms": round(elapsed_ms, 2),
        "cache": {
            "enabled": cache_aktif(),
            "hit": bool(result.get("cache_hit")),
            "threshold_l2": CACHE_THRESHOLD,
            "entries_in_index": int(getattr(QA_CACHE.index, "ntotal", 0)),
        },
        "triage": {"category": (result.get("category") or "").strip()},
        "guardrail": {"is_safe": bool(result.get("is_safe", True))},
        "retrieval": {
            "sop_chars": len(rd),
            "sop_preview": rd[:preview],
            "neo4j_context_chars": len(uc),
            "neo4j_preview": uc[:preview],
        },
        "normalized_issue_preview": ni[: min(preview, 280)],
    }


def emit_structured_ticket_log(ticket_id: str, observability: Dict[str, Any]) -> None:
    if not structured_log_enabled():
        return
    line = json.dumps(
        {"event": "ticket_processed", "ticket_id": ticket_id, "observability": observability},
        ensure_ascii=False,
    )
    print(line, flush=True)

#!/usr/bin/env python3
"""
Run golden-case scenarios against the LangGraph pipeline (direct invoke, no HTTP).

Usage (from repo root):
  python eval/run_eval.py
  python eval/run_eval.py --cases eval/custom_cases.json

Use the same .env (API keys, Neo4j, Chroma) as when running the API.

Cases with invoke_twice=true and expect_second.cache_hit=true require CAG_ENABLED=true
and the same Python process (in-memory RAM cache).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.graph import app_graph  # noqa: E402


def build_initial_state(case: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ticket_id": case.get("ticket_id", "eval-default"),
        "user_email": case["user_email"],
        "issue_text": case["issue_text"],
        "messages": [],
        "category": "",
        "retrieved_docs": "",
        "user_context": "",
        "draft_response": "",
        "is_safe": True,
        "cache_hit": False,
        "normalized_issue": "",
    }


def check_expect(result: Dict[str, Any], expect: Dict[str, Any]) -> List[str]:
    failures: List[str] = []
    if not expect:
        return failures

    if "cache_hit" in expect:
        if bool(result.get("cache_hit")) != bool(expect["cache_hit"]):
            failures.append(
                f"cache_hit: want {expect['cache_hit']!r}, got {result.get('cache_hit')!r}"
            )

    if "is_safe" in expect:
        if bool(result.get("is_safe")) != bool(expect["is_safe"]):
            failures.append(
                f"is_safe: want {expect['is_safe']!r}, got {result.get('is_safe')!r}"
            )

    if "sop_found" in expect:
        found = bool((result.get("retrieved_docs") or "").strip())
        if found != bool(expect["sop_found"]):
            failures.append(f"sop_found: want {expect['sop_found']!r}, got {found!r}")

    if "category_contains" in expect:
        cat = (result.get("category") or "").upper()
        needle = str(expect["category_contains"]).upper()
        if needle not in cat:
            failures.append(f"category: {result.get('category')!r} missing {needle!r}")

    if "user_context_contains" in expect:
        uc = result.get("user_context") or ""
        sub = expect["user_context_contains"]
        if sub not in uc:
            failures.append(f"user_context: missing substring {sub!r}")

    if "resolution_contains" in expect:
        text = result.get("draft_response") or ""
        items = expect["resolution_contains"]
        if isinstance(items, str):
            items = [items]
        for kw in items:
            if kw not in text:
                failures.append(f"resolution: missing {kw!r}")

    return failures


def run_case(case: Dict[str, Any]) -> Tuple[bool, List[str]]:
    state = build_initial_state(case)
    r1 = app_graph.invoke(state)
    failures: List[str] = []

    if case.get("invoke_twice"):
        first_expect = case.get("expect_first")
        if first_expect is None and case.get("expect") is not None:
            first_expect = case.get("expect")
        failures.extend([f"[invoke #1] {x}" for x in check_expect(r1, first_expect or {})])
        r2 = app_graph.invoke(build_initial_state(case))
        failures.extend([f"[invoke #2] {x}" for x in check_expect(r2, case.get("expect_second") or {})])
    else:
        failures.extend(check_expect(r1, case.get("expect") or {}))

    ok = len(failures) == 0
    return ok, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Run golden-case eval against app_graph.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=ROOT / "eval" / "golden_cases.json",
        help="Path ke JSON array definisi case",
    )
    args = parser.parse_args()

    raw = args.cases.read_text(encoding="utf-8")
    cases = json.loads(raw)
    if not isinstance(cases, list):
        print("cases file must be a JSON array", file=sys.stderr)
        return 2

    ran = 0
    passed = 0
    for case in cases:
        cid = case.get("id", "?")
        if not case.get("enabled", True):
            print(f"SKIP (disabled)  {cid}")
            continue
        ran += 1
        ok, failures = run_case(case)
        if ok:
            passed += 1
            print(f"PASS             {cid}")
        else:
            print(f"FAIL             {cid}")
            for fline in failures:
                print(f"                 - {fline}")

    print(f"\nSummary: {passed}/{ran} passed ({len(cases)} total entries)")
    return 0 if passed == ran else 1


if __name__ == "__main__":
    raise SystemExit(main())

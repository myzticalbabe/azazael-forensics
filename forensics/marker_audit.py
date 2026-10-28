#!/usr/bin/env python3
"""marker_audit.py — hunt the false-OK: mark_lesson_followed returning ok
while writing nothing.

The defect (2026-10-28, repro surface 5267): recall/fanout-sourced
surfaces return ok:true on mark but the row keeps followed=NULL.

Read-only triage over the PMB store (lesson_surfaces + mcp_calls).
Honesty note: mcp_calls records outcome='ok' with no surface id and no
args, so post-hoc forensics CANNOT distinguish a false-OK mark from a
mark never attempted (proven 2026-10-28: only a live experiment with
re-measurement told them apart, repro surface 5267). Buckets:
  LEGACY_RESURFACE  recall/fanout-family channel, followed IS NULL,
           older than --stale-days. Remedy is the same either way:
           re-surface through find_lessons. This bucket IS the churn queue.
  ORPHAN   honored-channel (or recent) surface, followed IS NULL, older
           than --stale-days. Neglect — mark or rebut it.

Source family is matched by substring: 'recall', 'fanout' count as
untrusted channels; 'find_lessons' is the honored channel.

Exits: 0 clean | 1 suspects/orphans over threshold | 2 environment.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from .portable import Environment, connect, locate_pmb_db

UNTRUSTED = ("recall", "fanout")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--stale-days", type=float, default=7.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        con = connect(locate_pmb_db(a.db))
    except Environment as e:
        print(f"ENVIRONMENT: {e}", file=sys.stderr)
        return 2
    try:
        has_calls = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='mcp_calls'").fetchone() is not None
        marks = []
        if has_calls:
            try:
                marks = [r[0] for r in con.execute(
                    "SELECT timestamp FROM mcp_calls WHERE "
                    "tool_name='mark_lesson_followed' AND "
                    "(success=1 OR success='1' OR success IS NULL) "
                    "ORDER BY timestamp")]
            except Exception:
                marks = []
        cutoff = time.time() - a.stale_days * 86400.0
        suspect, orphan = [], []
        rows = list(con.execute(
            "SELECT id, lesson_ulid, query, source, surfaced_at, "
            "followed FROM lesson_surfaces"))
        for r in rows:
            row = dict(r)
            if row["followed"] is not None:
                continue
            if (row["surfaced_at"] or 0) > cutoff:
                continue
            src = (row["source"] or "").lower()
            entry = {"id": row["id"], "source": row["source"],
                     "query": (row["query"] or "")[:100]}
            if any(k in src for k in UNTRUSTED):
                suspect.append(entry)
            else:
                orphan.append(entry)
    except Exception as e:
        print(f"ENVIRONMENT: store unreadable: {e}", file=sys.stderr)
        return 2
    out = {"legacy_resurface": suspect, "orphan_unmarked": orphan,
           "mark_calls_observed": len(marks)}
    if a.json:
        print(json.dumps(out, indent=1)[:4000])
    else:
        print(f"mark calls observed: {len(marks)}")
        print(f"LEGACY_RESURFACE (re-surface via find_lessons): {len(suspect)}")
        for s in suspect[:8]:
            print(f"  - surface {s['id']} [{s['source']}] {s['query']}")
        print(f"ORPHAN unmarked: {len(orphan)}")
        for s in orphan[:8]:
            print(f"  - surface {s['id']} [{s['source']}] {s['query']}")
    return 1 if (suspect or orphan) else 0


if __name__ == "__main__":
    raise SystemExit(main())

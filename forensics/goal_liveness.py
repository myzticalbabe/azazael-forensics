#!/usr/bin/env python3
"""goal_liveness.py — do open goals invite re-execution of settled work?

Flags (all read-only, PMB events store):
  STALE_OPEN   in_progress/pending goal at 0% older than --stale-days
  DUPLICATE    two+ open goals with the same normalized title
  SETTLED_OPEN title/content carries settled language
               (superseded/completed/done/cancelled/dead/retired/stale)
               while the goal is still open

Exits: 0 clean | 1 findings | 2 environment.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict

from .portable import Environment, connect, locate_pmb_db

SETTLED_WORDS = re.compile(
    r"superseded|completed|done|cancelled|dead|retired|stale|never re-?run|do not .*re-?execut",
    re.IGNORECASE,
)
NORM = re.compile(r"[^a-z0-9]+")


def norm_title(t: str) -> str:
    return NORM.sub(" ", (t or "").lower()).strip()


CLOSED = {"done", "completed", "closed", "cancelled", "superseded"}


def goal_status(meta: str) -> tuple[str, int]:
    # update_goal() mutates the goal row's own metadata in place AND appends
    # a goal_update history row pointing back via goal_ulid. The row is truth.
    try:
        m = json.loads(meta or "{}")
    except Exception:
        m = {}
    st = str(m.get("goal_status", m.get("status", "pending")))
    try:
        pr = int(m.get("goal_progress", m.get("progress", 0)) or 0)
    except Exception:
        pr = 0
    return st, pr


def collect(con) -> list[dict]:
    rows = []
    for r in con.execute(
        "SELECT ulid, content, metadata_json, timestamp FROM events "
        "WHERE event_type = 'goal'"
    ):
        rows.append(dict(r))
    return rows


def adjudicate(rows: list[dict], stale_days: float, now: float) -> dict:
    open_goals = []
    for u, r in [(x["ulid"], x) for x in rows]:
        st, pr = goal_status(r["metadata_json"])
        # A goal is open unless explicitly closed.
        if st in CLOSED:
            continue
        open_goals.append({"ulid": u, **r, "status": st, "progress": pr})
    findings = {"STALE_OPEN": [], "DUPLICATE": [], "SETTLED_OPEN": []}
    for g in open_goals:
        age_days = (now - g["timestamp"]) / 86400.0
        if g["progress"] == 0 and age_days > stale_days:
            findings["STALE_OPEN"].append({**g, "age_days": round(age_days, 1)})
        # Settled language on a FRESH goal is usually spec text (e.g. a new
        # detector goal describing what it hunts), not state. Only flag it
        # once the goal has survived past the stale horizon still open.
        text = f"{g['content']}"
        if age_days > stale_days and SETTLED_WORDS.search(text):
            findings["SETTLED_OPEN"].append({**g, "age_days": round(age_days, 1)})
    seen: dict[str, list[dict]] = defaultdict(list)
    for g in open_goals:
        seen[norm_title(g["content"])].append(g)
    for t, gs in seen.items():
        if len(gs) > 1 and t:
            findings["DUPLICATE"].append({"title": t, "ulids": [g["ulid"] for g in gs]})
    return {"open": len(open_goals), "findings": findings}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--stale-days", type=float, default=14.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        con = connect(locate_pmb_db(a.db))
    except Environment as e:
        print(f"ENVIRONMENT: {e}", file=sys.stderr)
        return 2
    out = adjudicate(collect(con), a.stale_days, time.time())
    n = sum(len(v) for v in out["findings"].values())
    if a.json:
        print(json.dumps(out, indent=1)[:4000])
    else:
        print(f"open goals: {out['open']}")
        for k, v in out["findings"].items():
            print(f"{k}: {len(v)}")
            for f in v[:8]:
                print(f"  - {f.get('content', f.get('title', ''))[:110]}")
    return 1 if n else 0


if __name__ == "__main__":
    raise SystemExit(main())

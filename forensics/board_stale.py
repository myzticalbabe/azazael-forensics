#!/usr/bin/env python3
"""board_stale.py — flag the append-only board's stale invitations.

The board (memorybus_queue) has push but no close: completed rows sit
beside open rows for the same work and fresh sessions redo settled tasks.

Read-only flags per normalized task key:
  CONTRADICTION  same key carries both settled language
                 (completed/done/blocked/superseded/cancelled) and live
                 language (need/open/in_progress/pending) across rows
  CHURN          same key appears >= --churn-n times (re-post loop)

Key = leading #TAG when present, else topic + first 40 chars of content.
Status words are matched case-insensitively in topic + content.

Exits: 0 clean | 1 findings | 2 environment.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict

from .portable import Environment, connect, locate_board_db

TAG = re.compile(r"#([A-Za-z][\w-]{2,}|[A-Za-z]{3,}|\d{4,})")
# A task key: alpha-led tag of 3+, or a long number (board rows like #45553).
# Deliberately excludes hex colors (#CC0000) and short numbers (#29).
SETTLED = re.compile(r"complet|done|block|supersede|cancel|retir|clos", re.IGNORECASE)
LIVE = re.compile(r"\bneed\b|open|in_progress|pending|in progress|pull|do\b", re.IGNORECASE)


def key_of(topic: str, content: str) -> str:
    # Structured rows carry their own identity — use it before falling
    # back to tag sniffing (which splinters truncated task_ids).
    try:
        d = json.loads(content or "")
        if isinstance(d, dict) and d.get("task_id"):
            return f"task:{d['task_id']}"
    except Exception:
        pass
    m = TAG.search(content or "")
    if m:
        return "#" + m.group(1).upper()
    return f"{topic}:{(content or '')[:40]}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board-db", default=None)
    ap.add_argument("--churn-n", type=int, default=3)
    ap.add_argument("--topics", default=None,
                    help="comma list; default every lane.* topic "
                    "(lane tasks/status/push). Bus telemetry topics "
                    "(nature.route.*, monitor.*) are excluded by default "
                    "— pass --topics explicitly to include them.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        con = connect(locate_board_db(a.board_db))
    except Environment as e:
        print(f"ENVIRONMENT: {e}", file=sys.stderr)
        return 2
    try:
        q = ("SELECT id, topic, content, source, session_id, timestamp "
             "FROM memorybus_queue")
        rows = [dict(r) for r in con.execute(q)]
    except Exception as e:
        print(f"ENVIRONMENT: board unreadable: {e}", file=sys.stderr)
        return 2
    if a.topics:
        want = {t.strip() for t in a.topics.split(",")}
        rows = [r for r in rows if r["topic"] in want]
    else:
        # Task state lives in tasks/push rows. *.status rows are heartbeat
        # snapshots (in_progress/completed as session posture, not task
        # state) and lane.all.announce is broadcast — both would drown the
        # signal with false contradictions.
        rows = [r for r in rows
                if ".tasks" in r["topic"] or ".push." in r["topic"]]
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[key_of(r["topic"], r["content"])].append(r)
    def stance(r: dict) -> str:
        # Row-level verdict: a row that is BOTH (closes one thing, opens
        # another) abstains — only clean settled-rows vs live-rows count.
        t = f"{r['topic']} {r['content']}"
        s, v = bool(SETTLED.search(t)), bool(LIVE.search(t))
        if s and not v:
            return "settled"
        if v and not s:
            return "live"
        return "mixed"
    contra, churn = [], []
    for k, rs in groups.items():
        if len(rs) < 2:
            continue
        stances = {stance(r) for r in rs}
        if "settled" in stances and "live" in stances:
            contra.append({"key": k, "rows": len(rs),
                           "ids": [r["id"] for r in rs][:10]})
        if len(rs) >= a.churn_n:
            churn.append({"key": k, "rows": len(rs),
                          "ids": [r["id"] for r in rs][:10]})
    out = {"keys": len(groups), "contradictions": contra, "churn": churn}
    if a.json:
        print(json.dumps(out, indent=1)[:4000])
    else:
        print(f"task keys: {len(groups)}")
        print(f"CONTRADICTION: {len(contra)}")
        for c in contra[:10]:
            print(f"  - {c['key']} ({c['rows']} rows)")
        print(f"CHURN (>={a.churn_n} rows): {len(churn)}")
        for c in churn[:10]:
            print(f"  - {c['key']} ({c['rows']} rows)")
    return 1 if (contra or churn) else 0


if __name__ == "__main__":
    raise SystemExit(main())

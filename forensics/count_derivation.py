#!/usr/bin/env python3
"""count_derivation.py — do the numbers in prose match the artifacts?

A manifest (JSON) lists derivations to check:

  {"checks": [
    {"id": "edges",
     "file": "01_verified/network_edges_proofed.json",
     "query": "len(edges)",
     "expected": 118},
    {"id": "tally-verified",
     "file": "01_verified/proof_audit.json",
     "query": "get(summary.grades.verified)",
     "expected": 58},
    {"id": "ledger-rows",
     "file": "01_verified/edge_proof_ledger.md",
     "query": "lines(starts='| ', skip_header=2)",
     "expected": 118},
  ],
  "claims": [
    {"id": "canon-118", "file": "AGENTS.md", "pattern": "118 edges"}
  ]}

Query mini-language (read-only):
  len(dotted.path)          list/dict length at path
  count(dotted.path.to.list[field=value])   rows matching field==value
  get(dotted.path.to.key)   scalar value
  lines(starts='| ', skip_header=N)  markdown-table data rows (files)

claim entries assert the number is DECLARED in prose (presence only —
presence is not truth; the artifact rows above are truth).

Exits: 0 all derivations hold | 1 any mismatch | 2 environment.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .portable import Environment


def resolve(base: Path, rel: str) -> Path:
    p = (base / rel).resolve()
    if not p.is_file():
        raise Environment(f"artifact not found: {rel} (under {base})")
    return p


def dotted(obj, path: str):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise Environment(f"path not found in artifact: {path}")
    return cur


def ev(query: str, artifact: Path):
    text = artifact.read_text(encoding="utf-8", errors="replace")
    m = re.fullmatch(r"len\((.+)\)", query.strip())
    if m:
        data = json.loads(text)
        return len(dotted(data, m.group(1)))
    m = re.fullmatch(r"count\((.+)\[(\w+)=(.+)\]\)", query.strip())
    if m:
        data = json.loads(text)
        rows = dotted(data, m.group(1))
        return sum(1 for r in rows if str(r.get(m.group(2))) == m.group(3))
    m = re.fullmatch(r"get\((.+)\)", query.strip())
    if m:
        return dotted(json.loads(text), m.group(1))
    m = re.fullmatch(r"lines\(starts='(.*)', skip_header=(\d+)\)", query.strip())
    if m:
        rows = [ln for ln in text.splitlines() if ln.startswith(m.group(1))]
        return max(0, len(rows) - int(m.group(2)))
    raise Environment(f"unsupported query (add it, don't fake it): {query}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        root = Path(a.root).resolve()
        man = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ENVIRONMENT: {e}", file=sys.stderr)
        return 2
    results = []
    try:
        for c in man.get("checks", []):
            try:
                got = ev(c["query"], resolve(root, c["file"]))
                ok = got == c["expected"]
                results.append({"id": c["id"], "ok": ok, "got": got,
                                "expected": c["expected"]})
            except Environment as e:
                results.append({"id": c["id"], "ok": False, "error": str(e)})
        for c in man.get("claims", []):
            try:
                text = resolve(root, c["file"]).read_text(
                    encoding="utf-8", errors="replace")
                if c.get("absent"):
                    gone = c["pattern"] not in text
                    results.append({
                        "id": c["id"], "ok": gone,
                        "note": "retracted-from-prose" if gone
                        else "STALE CLAIM STILL PRESENT"})
                    continue
                found = c["pattern"] in text
                results.append({"id": c["id"], "ok": found,
                                "note": "declared-in-prose (presence, not truth)"})
            except Environment as e:
                results.append({"id": c["id"], "ok": False, "error": str(e)})
    except Environment as e:
        print(f"ENVIRONMENT: {e}", file=sys.stderr)
        return 2
    bad = [r for r in results if not r["ok"]]
    if a.json:
        print(json.dumps(results, indent=1))
    else:
        for r in results:
            mark = "OK " if r["ok"] else "FAIL"
            print(f"{mark} {r['id']}: {r.get('got', r.get('note', r.get('error')))}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

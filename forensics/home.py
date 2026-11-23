#!/usr/bin/env python3
"""home.py — every azazael capability, reachable from the portable tree.

The tree does not duplicate the home. It REACHES it: this adapter resolves
the azazael checkout (AZAZAEL_HOME env, else the sibling ../azazael
convention), inventories all 52 named forensic tools, and runs any of them
with arguments passed through and exit codes preserved.

Only 4 of the 52 ship with this tree. The other 48 resolve inside the
azazael home checkout, so a standalone clone delivers 4 detectors and
exits 2 on `inventory` until AZAZAEL_HOME (or ../azazael) names a home.

No copies, no drift, no palimpsest: one source of truth (the home tree),
one calling convention (this module). When the home is absent the adapter
fails closed (exit 2), never a false green.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

TREE_ROOT = Path(__file__).resolve().parent.parent

# name -> (class, lines). Classes: native (lives in this tree),
# portable (home original, no azazael/model imports — portable as-is),
# coupled (home original, needs azazael runtime or a model).
# Line counts measured 2026-10-28; the inventory command re-checks presence.
TOOLS: dict[str, tuple[str, int]] = {
    # native
    "goal_liveness": ("native", 0), "marker_audit": ("native", 0),
    "count_derivation": ("native", 0), "board_stale": ("native", 0),
    # portable home originals
    "absent_triage": ("portable", 169), "aggregate_suite_gate": ("portable", 609),
    "artifact_freshness": ("portable", 312), "audit_chain_repair": ("portable", 378),
    "audit_parseable_files": ("portable", 292), "cain_full_audit": ("portable", 49),
    "cain_render_gate": ("portable", 131), "cain_verify_analysis": ("portable", 61),
    "capability_liveness": ("portable", 373), "claim_guard": ("portable", 268),
    "dict_key_triage": ("portable", 219), "encoding_audit": ("portable", 755),
    "failure_evidence_gate": ("portable", 428), "fitness_arm_liveness": ("portable", 228),
    "index_drift_check": ("portable", 138), "lesson_liveness": ("portable", 413),
    "mesh_function_preflight": ("portable", 1843), "orphan_triage": ("portable", 434),
    "package_audit_315": ("portable", 87), "paradigm_gate": ("portable", 100),
    "refresh_all": ("portable", 228), "rule_enforcement_audit": ("portable", 351),
    "silent_failure_audit": ("portable", 167), "technique_exercise_only_audit": ("portable", 204),
    "training_intake_audit": ("portable", 455), "twelve_factor_audit": ("portable", 571),
    "type_check_gate": ("portable", 424), "vacuous_check_audit": ("portable", 307),
    "verify_hashes": ("portable", 111), "verify_mesh_html": ("portable", 353),
    "verify_p9_drill": ("portable", 228), "verify_pipeline": ("portable", 308),
    "wire_evidence_audit": ("portable", 264),
    # coupled home originals (need azazael runtime or a model)
    "adoption_census": ("coupled", 1217), "anchor_runtime_gate": ("coupled", 207),
    "anti_pattern_gate": ("coupled", 460), "audit_append_stress": ("coupled", 130),
    "canon_drift_check": ("coupled", 372), "evolution_chain_audit": ("coupled", 221),
    "gephi_mesh_pipeline": ("coupled", 676), "harvest_compliance": ("coupled", 128),
    "mesh_repaird": ("coupled", 154), "orphan_scan": ("coupled", 237),
    "staged_scanner_gate": ("coupled", 129), "transcript_ap5_gate": ("coupled", 869),
    "verify_engram_mcp": ("coupled", 774), "verify_python_stack": ("coupled", 194),
    "verify_supervisor_load": ("coupled", 158),
}


class Environment(Exception):
    pass


def locate_home(explicit: str | None = None) -> Path:
    if explicit:
        p = Path(explicit)
        if (p / "tools").is_dir():
            return p
        raise Environment(f"azazael home not found at: {explicit}")
    env = os.environ.get("AZAZAEL_HOME")
    if env and (Path(env) / "tools").is_dir():
        return Path(env)
    sib = TREE_ROOT.parent / "azazael"
    if (sib / "tools").is_dir():
        return sib
    raise Environment(
        "azazael home not located. Set AZAZAEL_HOME (checkout root holding "
        "tools/). Refusing to report PASS without the home tree.")


def inventory(home: Path) -> dict:
    rows = []
    for name, (cls, lines) in sorted(TOOLS.items()):
        if cls == "native":
            present = (TREE_ROOT / "forensics" / f"{name}.py").is_file()
            rows.append({"tool": name, "class": cls, "present": present,
                         "runs_from": "tree"})
        else:
            p = home / "tools" / f"{name}.py"
            rows.append({"tool": name, "class": cls, "present": p.is_file(),
                         "runs_from": "home" if p.is_file() else "missing"})
    return {"home": str(home), "tools": rows,
            "present": sum(1 for r in rows if r["present"]),
            "total": len(rows)}


def run_tool(home: Path, name: str, args: list[str]) -> int:
    if name not in TOOLS:
        print(f"ENVIRONMENT: unknown tool '{name}' (not in registry).",
              file=sys.stderr)
        return 2
    cls, _ = TOOLS[name]
    if cls == "native":
        target = [sys.executable, "-m", f"forensics.{name}", *args]
        cwd = str(TREE_ROOT)
    else:
        p = home / "tools" / f"{name}.py"
        if not p.is_file():
            print(f"ENVIRONMENT: {name}.py absent from home {home}.",
                  file=sys.stderr)
            return 2
        target = [sys.executable, str(p), *args]
        cwd = str(home)
    try:
        r = subprocess.run(target, cwd=cwd)
        return r.returncode
    except Exception as e:
        print(f"ENVIRONMENT: failed to launch {name}: {e}", file=sys.stderr)
        return 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory")
    rp = sub.add_parser("run")
    rp.add_argument("tool")
    rp.add_argument("args", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    try:
        home = locate_home(a.home)
    except Environment as e:
        print(f"ENVIRONMENT: {e}", file=sys.stderr)
        return 2
    if a.cmd == "inventory":
        inv = inventory(home)
        print(f"home: {inv['home']}")
        print(f"present: {inv['present']}/{inv['total']}")
        missing = [r["tool"] for r in inv["tools"] if not r["present"]]
        for m in missing:
            print(f"  MISSING: {m}")
        by_cls: dict[str, int] = {}
        for r in inv["tools"]:
            by_cls[r["class"]] = by_cls.get(r["class"], 0) + 1
        print("classes:", by_cls)
        return 0 if not missing else 1
    return run_tool(home, a.tool, [x for x in (a.args or []) if x != "--"])


if __name__ == "__main__":
    raise SystemExit(main())

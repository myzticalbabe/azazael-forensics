"""portable.py — machine-independent store locators for the forensic tree.

Precedence for every store: explicit argument > environment variable >
sibling-checkout convention (../azazael next to this tree) > fail closed.

There are NO machine-default paths in this tree. A detector that cannot
locate its store exits ENVIRONMENT (2), never a false green.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

TREE_ROOT = Path(__file__).resolve().parent.parent
SIBLING_AZAZAEL = TREE_ROOT.parent / "azazael"


class Environment(Exception):
    """Raised when a store cannot be located. Callers map to exit 2."""


def locate_pmb_db(explicit: str | None = None) -> Path:
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p
        raise Environment(f"PMB db not found at explicit path: {explicit}")
    env = os.environ.get("PMB_WORKSPACE_DIR")
    if env:
        p = Path(env) / "events.sqlite"
        if p.is_file():
            return p
        raise Environment(f"PMB db not found under PMB_WORKSPACE_DIR={env}")
    raise Environment(
        "PMB store not located. Pass --db or set PMB_WORKSPACE_DIR "
        "(the directory containing events.sqlite). Refusing to report "
        "PASS on a store that is not there."
    )


def locate_board_db(explicit: str | None = None) -> Path:
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p
        raise Environment(f"Board db not found at explicit path: {explicit}")
    env = os.environ.get("FORENSICS_BOARD_DB")
    if env and Path(env).is_file():
        return Path(env)
    # azazael MemoryBus convention, replicated dependency-free:
    # AZAZAEL_MEMORY_DIR/telemetry_store.db else ~/.azazael/telemetry_store.db
    azdir = os.environ.get("AZAZAEL_MEMORY_DIR")
    for p in (([Path(azdir) / "telemetry_store.db"] if azdir else [])
              + [Path.home() / ".azazael" / "telemetry_store.db"]):
        if p.is_file():
            return p
    # Sibling-checkout convention: ask azazael's MemoryBus directly.
    try:
        import sys
        cand = SIBLING_AZAZEL / "src"
        if cand.is_dir() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))
        from CORE.MemoryBus import _MEMORYBUS_DB_PATH as mbp  # type: ignore
        if Path(mbp).is_file():
            return Path(mbp)
    except Exception:
        pass
    raise Environment(
        "Board store not located. Pass --board-db or set FORENSICS_BOARD_DB "
        "(the memorybus sqlite file). Refusing to report PASS on a store "
        "that is not there."
    )


def connect(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db), timeout=15.0)
    con.row_factory = sqlite3.Row
    return con

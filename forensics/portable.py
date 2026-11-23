"""portable.py — machine-independent store locators for the forensic tree.

Precedence for every store: explicit argument > environment variable >
fail closed. There is no third step -- a store is never guessed from the
machine the detector happens to be running on.

There are NO machine-default paths in this tree. A detector that cannot
locate its store exits ENVIRONMENT (2), never a false green.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

TREE_ROOT = Path(__file__).resolve().parent.parent


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
    # AZAZAEL_MEMORY_DIR/telemetry_store.db, and only that.
    azdir = os.environ.get("AZAZAEL_MEMORY_DIR")
    if azdir:
        p = Path(azdir) / "telemetry_store.db"
        if p.is_file():
            return p
    # Deliberately NOT extended with the ~/.azazael machine default, and NOT
    # resolved by importing CORE.MemoryBus. The first is exactly the thing this
    # module exists to have none of. The second is the monorepo dependency this
    # module exists to avoid, and an import inside a bare try/except is a
    # failure that can never be seen: it works on the author's machine and
    # fails silently everywhere else. Both are gone.
    raise Environment(
        "Board store not located. Pass --board-db, or set FORENSICS_BOARD_DB "
        "(the memorybus sqlite file) or AZAZAEL_MEMORY_DIR (the directory "
        "holding telemetry_store.db). Refusing to report PASS on a store "
        "that is not there."
    )


def connect(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db), timeout=15.0)
    con.row_factory = sqlite3.Row
    return con

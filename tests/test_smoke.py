"""Smoke: every detector imports, parses --help, and exits 2 on a
missing store (fail-closed, never a false green)."""
import subprocess
import sys

MODS = ["forensics.goal_liveness", "forensics.count_derivation",
        "forensics.marker_audit", "forensics.board_stale"]


def test_imports():
    for m in MODS:
        __import__(m)


def test_help():
    for m in MODS:
        r = subprocess.run([sys.executable, "-m", m, "--help"],
                           capture_output=True, text=True)
        assert r.returncode == 0, (m, r.stderr[:200])


def test_fail_closed_missing_store(tmp_path):
    cases = [
        (["forensics.goal_liveness", "--db", str(tmp_path / "nope.sqlite")],),
        (["forensics.marker_audit", "--db", str(tmp_path / "nope.sqlite")],),
        (["forensics.board_stale", "--board-db", str(tmp_path / "nope.sqlite")],),
        (["forensics.count_derivation", str(tmp_path / "nope.json"),
          "--root", str(tmp_path)],),
    ]
    for (args,) in cases:
        r = subprocess.run([sys.executable, "-m", *args],
                           capture_output=True, text=True)
        assert r.returncode == 2, (args, r.returncode, r.stderr[:200])

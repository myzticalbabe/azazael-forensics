"""home.py adapter — registry integrity (no home checkout needed)."""
from forensics.home import TOOLS


def test_registry_covers_all_classes():
    classes = {c for _, (c, _) in TOOLS.items()}
    assert classes == {"native", "portable", "coupled"}, classes


def test_registry_counts():
    by = {}
    for _, (c, _) in TOOLS.items():
        by[c] = by.get(c, 0) + 1
    assert by["native"] == 4, by
    assert by["portable"] == 33, by
    assert by["coupled"] == 15, by
    assert sum(by.values()) == 52, by


def test_no_orphan_references():
    # every tool the docs promise is reachable must be registered
    for name in ("claim_guard", "orphan_triage", "mesh_function_preflight",
                 "lesson_liveness", "verify_p9_drill", "anti_pattern_gate",
                 "goal_liveness", "board_stale"):
        assert name in TOOLS, name

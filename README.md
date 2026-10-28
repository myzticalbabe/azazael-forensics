# azazael-forensics — standalone portable investigation tree

Yggdrasil Cleave #11. Sibling of `azazael/`, never inside it: this tree
must run on any machine with nothing but Python 3.10+ stdlib. No network,
no model calls, no machine-default paths.

## The portability contract (`forensics/portable.py`)

Every detector resolves stores in one order: explicit argument >
environment variable > sibling-checkout convention (`../azazael`) >
**fail closed**. Missing store = exit `2` (ENVIRONMENT), never a green.

- `PMB_WORKSPACE_DIR` — directory holding PMB `events.sqlite`
- `FORENSICS_BOARD_DB` — memorybus sqlite file (board detector)
- Detectors run anywhere: `python -m forensics.goal_liveness --help`

## Detectors (each: 0 clean · 1 findings · 2 environment)

| Module | Hunts | Owning debt |
|---|---|---|
| `goal_liveness` | stale @0% opens, duplicate titles, settled-but-open | 282 orphans; #1039-as-written |
| `marker_audit` | false-OK marks (recall/fanout, ok-without-write) | PMB marker defect, repro 5267 |
| `count_derivation` | prose numbers vs artifact JSON/markdown counts | the 120-that-never-was |
| `board_stale` | duplicate keys, completed-vs-open contradictions | 50-row append-only board |

Older siblings already portable (no hardcodes): `claim_guard`,
`orphan_triage`, `anti_pattern_gate`, `mesh_function_preflight`.
Already env-first: `lesson_liveness`, `verify_p9_drill`.
Known owed extensions (queued, not here): orphan_triage → goal-pin
checks; claim_guard → JSON count cross-checks.

## Use

```bash
python -m forensics.goal_liveness --stale-days 14
python -m forensics.marker_audit --stale-days 7
python -m forensics.board_stale
python -m forensics.count_derivation manifest.json --root /path/to/tree
python -m pytest tests/ -q
```

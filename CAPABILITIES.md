# Capability coverage — tree vs azazael (2026-10-28, measured; reframed same day)

CORRECTION (review, operator: "why is it a defect layer?"): the tree was
framed as a defect-detector layer. Wrong. The assignment is the full
portable forensic capability — every azazael investigation tool reachable
from anywhere, via native ports plus `forensics/home.py`, which inventories
and runs all 49 named home tools with no copies and no drift. Heavy
machinery stays home and RUNS through the adapter; nothing is unreachable.

Import-level sieve of azazael's 49 named forensic tools (`tools/*.py`
matching audit|gate|verify|liveness|fresh|provenance|claim|orphan|mesh|
lesson|training|compliance|triage|drift|canon|adopt|census|ratchet|sentinel|origin):

## Native to this tree (4)
`goal_liveness`, `marker_audit`, `count_derivation`, `board_stale`.

## Referenced, live in azazael, already portable (5)
`claim_guard` (268), `orphan_triage` (434),
`mesh_function_preflight` (1843), `lesson_liveness` (413),
`verify_p9_drill` (228). No hardcodes or env-first; usable as-is.
CORRECTION: `anti_pattern_gate` (460) was listed here — wrong, the sieve
shows it imports CORE (coupled). Moved below.

## Portable candidates — queued for Wave ports (28)
Small (<250): `paradigm_gate` (100), `verify_hashes` (111),
`cain_render_gate` (131), `index_drift_check` (138),
`package_audit_315` (87), `silent_failure_audit` (167),
`technique_exercise_only_audit` (204), `dict_key_triage` (219),
`fitness_arm_liveness` (228), `refresh_all` (228),
`audit_parseable_files` (292), `verify_pipeline` (308),
`vacuous_check_audit` (307), `wire_evidence_audit` (264).
Medium (300–600): `artifact_freshness` (312), `audit_chain_repair` (378),
`capability_liveness` (373), `rule_enforcement_audit` (351),
`failure_evidence_gate` (428), `training_intake_audit` (455),
`aggregate_suite_gate` (609), `twelve_factor_audit` (571),
`encoding_audit` (755), `type_check_gate` (424),
`verify_mesh_html` (353), `absent_triage` (169), `cain_verify_analysis` (61),
`cain_full_audit` (49) — 14 small + 14 medium = 28 (header said 27; corrected).
Each port = copy, strip machine defaults to env-first, add smoke test.

## Coupled — stay home, RUN through `forensics/home.py` (15)
azazael-runtime-bound: `adoption_census`, `anchor_runtime_gate`,
`anti_pattern_gate` (moved here — imports CORE),
`audit_append_stress`, `canon_drift_check`, `evolution_chain_audit`,
`gephi_mesh_pipeline`, `harvest_compliance`, `mesh_repaird`, `orphan_scan`,
`staged_scanner_gate`, `verify_python_stack`, `verify_supervisor_load`.
Model/MCP-bound: `transcript_ap5_gate`, `verify_engram_mcp`.
`python -m forensics.home inventory` proves presence;
`python -m forensics.home run <tool> [args...]` runs any of them with
exit codes preserved. Absent home = exit 2, never green.

## Entire classes not in this tree (by design)
Memory apparatus (PMB/Engram MCP servers), compliance enforcement
(sentinel, ratchet, VLP), training intake + GRPO loop, codegraph,
render pipeline. The tree *checks outputs*; the home *does work*.

## Rule
A capability lands here only with: zero machine defaults, 0/1/2 exits,
smoke test, and a live-store proof run. No ports by copy-paste.

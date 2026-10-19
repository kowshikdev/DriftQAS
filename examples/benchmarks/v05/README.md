# v0.5 multi-edge locality study

The [protocol](../../../docs/multiedge_protocol.md), full grid and deterministic gate were
committed as `e05a86730496bfff27528b67d21ee0b32381783f` before development screening.

`screen/` is a complete, checksum-sealed **development-only** audit dataset, including
20 prepared banks with trained parameters and compiled QASM, 1,920 audit rows, transition
metrics, costs, declaration and completion receipt. `verify-screen` verifies these artifacts;
it is not an online policy suite or final controller evidence.

All four field/training cells are retained. Field 0.5 has no winner-set reversals at either
training cap. Field 1.5 has locality opportunities on all five development seeds for both
changed edges, at both caps. There are zero zero-exposure invariance violations.
The fixed cheaper-first rule therefore selects **field 1.5, cap 120**. The auditable
decision is in `selection.json`; it does not use controller performance.

The selected suite in `configs/locality_ising.yaml` keeps stable/end-edge/central-edge
cases and all eight policies. Its primary comparison is component-matched racing minus
**global matching**, not blind reuse. The freeze binds source, runtime, budgets, cases,
primary estimand and disjoint seed partitions before the 20-seed held-out run. The separate
calibration partition is reserved and will not be executed; no v0.4 temperature is reused.

Screen preparation used **43,311 ideal objective calls** and **480 distinct exact audit
evaluations**, with zero online shots. These are development costs, separate from online
policy costs. A passing mechanistic gate is not evidence that a controller beats a baseline.
See `screen/report.md` for every cell, including the failed low-field cells.

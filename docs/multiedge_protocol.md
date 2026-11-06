# Multi-edge locality milestone (v0.5)

The next question is whether circuit-specific evidence reuse helps **beyond global
matching**, rather than only beating stale blind reuse. The v0.4 H₂ study has one CX
edge, while its four-qubit Ising development banks had no true winner changes. Those
results remain unchanged. This milestone first checks whether a multi-edge library
offers a meaningful test of the locality mechanism.

## Development screen declared before execution

`configs/locality_screen.yaml` declares the entire grid: four-qubit open-boundary Ising,
fields 0.5 and 1.5, ideal training caps 120 and 480 calls per candidate, eight stratified
candidates, four epochs, and stable/abrupt end-edge/abrupt central-edge cases. The base
CX depolarizing probability is 0.005 and the abrupt stress probability is 0.12. This
stress test does not characterize typical hardware. Development seeds are 4001–4005;
calibration 5001–5020 and test 6001–6020 are disjoint and reserved.

The new screen uses exact audits with zero online shots and executes no controller.
It shares identical banks across cases and caches identical noise conditions. Preparation
and audit costs are recorded explicitly. These savings apply only to offline screening;
the existing online suite still prepares its shared policy bank separately per episode.
Every setting, failed cell, raw bank/QASM and audit is retained. Screening is rejected
for non-development partitions before any output creation. This is a consistency guard,
not proof an operator has never inspected a seed.

## Mechanistic gate and deterministic selection

Use energy tolerance `1e-8`. A **winner-set reversal** requires every candidate that was
optimal within tolerance before a transition to have positive current regret greater
than tolerance. This stricter definition avoids reversals created by arbitrary choices
among tied former winners; it does not relabel the v0.4 diagnostics.

A **locality opportunity** additionally requires at least one current tolerance-optimal
candidate with a **nonempty compiled CX footprint** whose used-edge error rates did not
change. Product-only candidates do not satisfy this condition. Nonempty CX exposure does
not certify state entanglement. Zero exposure must imply unchanged audited energy under
this CX-only model; a violation fails the screen and preserves its failure.

An admissible field/training cell must have locality opportunities in **at least three
of five development seeds for each of the end-edge and central-edge abrupt cases**.
No invariance violation is allowed. Choose the first admissible cell in this fixed order:

1. field 0.5, cap 120;
2. field 1.5, cap 120;
3. field 0.5, cap 480;
4. field 1.5, cap 480.

This chooses a lower-cost admissible setting before comparing controllers. Selection
uses only development audits, never controller performance, calibration or test outcomes.
If no cell is admissible, **stop before the reserved seeds** and report the failed gate.
Do not extend the grid until a desirable result appears, or force a superiority claim.

## Conditional frozen comparison

Only if the gate passes, construct a separate three-case suite for the chosen cell:
stable, abrupt end-edge (0–1), and abrupt central-edge (1–2). Keep all eight controls:
original GP reuse/DriftQAS, ideal-only, fresh/blind/global racing, component-matched racing,
and uniform component matching. All use the same prepared bank and 1,024-shot epoch cap,
including protected fresh confirmation. Low/high batches are 32/128 shots per measurement
group, with racing beta 2 and SD floor 0.002. The tighter cap is declared before screening;
it is not selected using policy outcomes. All grouping and accounting rules remain intact.

The single primary contrast is `driftqas_racing - global_racing` in exact mean selection
regret, averaging all epochs and all three cases within seed before resampling seed
clusters (10,000 percentile bootstrap samples, seed 2026). All cases and all 20 fresh test
seeds remain in the report. Other contrasts are descriptive and unadjusted. Actual shots,
fresh confirmation, raw prediction coverage, and the negative controls must remain visible.

Commit the selected suite, source/environment freeze and development findings before
running test seeds. Do not tune the controller or choose test seeds after seeing outcomes.
The calibration partition is **reserved but not executed in this selection-only milestone**;
v0.4 fitted scales must not be transferred to a new task. No calibrated interval claim
is made for the new Ising study. A future calibration study needs its own pre-test artifact
and fresh test partition. Existing freeze validation still binds every declared partition.

Even a passing screen establishes only an adaptation opportunity, not a controller
advantage. A null or adverse global-comparator test result is a valid final finding.
Candidates and parameters remain fixed; unrestricted search, noisy online training,
uncertain calibration, readout/crosstalk and physical hardware remain outside this milestone.

## Commands

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m driftqas screen-suite --config configs/locality_screen.yaml --plan
python -m driftqas screen-suite --config configs/locality_screen.yaml --output results/locality-screen
python -m driftqas verify-screen --screen-dir results/locality-screen
python -m driftqas select-locality --config configs/locality_screen.yaml \
  --screen-dir results/locality-screen --output results/locality-selection.json
```

The screen's explicit canonical-artifact receipt includes every prepared bank, full audit
grid, transition metrics, declaration, summary and status. Incidental runtime files are
excluded; genuine content changes, missing files, symlinks and inconsistent identities fail
verification. Failed screens cannot be presented as completed studies or silently overwritten.

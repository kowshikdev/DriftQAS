# Verified v0.3 development examples

These are compact exports from actual simulator suites using the final v0.3 source. Both
suites completed all declared episodes, passed database/JSONL consistency and artifact
checks, and then resumed without rerunning completed episodes. Full raw event ledgers,
compiled circuits and completion receipts are generated locally, not included in these
compact exports. These folders therefore are not complete inputs to `analyze-suite`.

| Folder | Configuration | Cases | Seeds | Policies | Primary DriftQAS minus reuse |
|---|---|---:|---:|---:|---|
| `smoke/` | `configs/suite_smoke.yaml` | 2 H2 | 3 | 9 | 0; interval withheld |
| `pilot/` | `configs/suite_pilot.yaml` | 2 four-qubit Ising | 5 | 9 | 0; observed bootstrap interval [0, 0] |

All five Ising seed clusters tied on the primary metric. The zero-width empirical interval
reflects those observed ties; it does not prove universal equivalence or sufficient power.
The study remains a small development pilot. Held-out seeds have not been run here.

Each folder includes the frozen suite manifest, human-readable report, per-episode metrics,
policy summaries, and paired comparisons. Negative paired regret differences favor DriftQAS.
All cases and controls are retained, including stable conditions and unfavorable comparisons.

Reproduce in a fresh output directory:

```bash
python -m driftqas suite --config configs/suite_smoke.yaml --output results/reproduce-smoke
python -m driftqas suite --config configs/suite_pilot.yaml --output results/reproduce-pilot
python -m driftqas suite --config configs/suite_pilot.yaml --output results/reproduce-pilot --resume
```

Local validation limited BLAS/OpenMP thread counts to one; Qiskit Aer already limits its
simulation threads to one. Timing is machine-dependent and is not a hardware-speedup claim.
See [the protocol](../../docs/benchmark_protocol.md) and
[development interpretation](../../docs/development_results.md).

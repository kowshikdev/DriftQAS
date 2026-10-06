# Development results

The first two tables are actual v0.2 single-seed local simulations. The v0.3 repeated-seed
pilot below is also development evidence, not a final research comparison.

Python 3.12; Qiskit 2.5.2; Aer 0.17.2. The checked-in manifests record the configuration, package versions, and source digest.

Selection regret uses an independent density-matrix audit of the frozen candidate bank. Lower is better. Confirmation measurements were taken after the recommendation was locked.

## H2

| Policy | Mean epoch regret | Final epoch regret | Total online shots |
|---|---:|---:|---:|
| restart | 0.003183 | 0.000000 | 24268 |
| reuse | 0.003183 | 0.000000 | 24268 |
| driftqas | 0.011109 | 0.011889 | 24268 |

Shared ideal bank preparation: 542 objective calls. This is reported separately from online-shot totals.

![H2 development comparison](../examples/development/h2-comparison.png)

## Four-qubit Ising

| Policy | Mean epoch regret | Final epoch regret | Total online shots |
|---|---:|---:|---:|
| random | 0.014246 | 0.013827 | 65380 |
| restart | 0.005963 | 0.023851 | 65432 |
| reuse | 0.006914 | 0.013827 | 65432 |
| global_forgetting | 0.003457 | 0.000000 | 65484 |
| periodic_refresh | 0.006914 | 0.013827 | 65432 |
| driftqas | 0.006914 | 0.013827 | 65484 |

Shared ideal bank preparation: 1871 objective calls. This is reported separately from online-shot totals.

![Four-qubit Ising development comparison](../examples/development/ising-comparison.png)

## Interpretation

DriftQAS did not consistently outperform the controls. It had higher mean regret in the H2 smoke run and matched unchanged reuse in the four-qubit run; global forgetting had lower mean regret in that Ising run. These observations validate the executable comparison pipeline, not the proposed research benefit.

No inference about statistical superiority should be made from one seed. The next research steps are development-only tuning, held-out repeated-seed comparisons, ablations, and tests of whether footprint exposure predicts real performance changes. Keep these unfavorable results visible.

The online selector uses a staged heuristic and a fixed-kernel GP. Its relevance scales and uncertainty have not been empirically calibrated. The broader project plan remains a research agenda.

Reproduce with `configs/smoke.yaml` or `configs/ising.yaml` using a fresh output directory. The run exports raw counts and SQLite events locally; compact summaries and figures are checked in here.

## v0.3 repeated-seed pilot

The untuned Ising pilot used four qubits, field 0.5, six candidates, 80 training calls per
candidate, three epochs, a 4096-shot epoch limit, stable and abrupt conditions, all nine policies,
and development seeds 7, 19, 31, 43, 59. Every declared pair completed and passed event/export
and artifact checks; resumption skipped all completed episodes. No held-out seeds were run.

| Policy | Mean selection regret | Budget utilization | Confirmation coverage | Model coverage |
|---|---:|---:|---:|---:|
| random | 0.014300 | 98.5% | 93.3% | 93.3% |
| restart | 0.018608 | 98.5% | 93.3% | 96.7% |
| reuse | 0.010394 | 98.3% | 96.7% | 90.0% |
| global_forgetting | 0.010394 | 98.3% | 96.7% | 93.3% |
| periodic_refresh | 0.010394 | 98.3% | 96.7% | 90.0% |
| driftqas | 0.010394 | 98.3% | 96.7% | 93.3% |
| driftqas_global_relevance | 0.010394 | 98.3% | 96.7% | 93.3% |
| driftqas_no_refresh | 0.010394 | 98.3% | 96.7% | 93.3% |
| driftqas_fixed_shots | 0.011986 | 95.0% | 93.3% | 90.0% |

The primary paired DriftQAS-minus-reuse mean difference was **0** across all five seed clusters.
The empirical percentile interval was **[0, 0]** because all five observed paired differences
were zero. This does not prove universal equivalence, adequate power, or a benefit from the
proposed mechanism. Case-specific comparisons and secondary controls remain visible.

Coverage concerns nominal 95% intervals on locked recommendations. These small, correlated
development observations do not certify calibration. In the accompanying three-seed H2 suite,
DriftQAS model coverage was only 66.7%, despite tying reuse on regret. That is a concrete reason
to investigate uncertainty and exposure behavior before stronger research claims.

The next experimental step is to check whether footprint exposure predicts meaningful changes
and whether the bank/profile/budget regime actually separates the mechanisms. Use development
data for that investigation, then freeze the study before running held-out seeds. Do not tune
against held-out outcomes to manufacture a win.

Compact exports and manifests are in [examples/benchmarks](../examples/benchmarks).
Reproduce with `configs/suite_smoke.yaml` and `configs/suite_pilot.yaml`. The proposed full
matrix is in `configs/benchmark_ising.yaml`; it has not been executed as a final study.

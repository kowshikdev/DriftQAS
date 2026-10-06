# v0.4 exposure study

These folders contain compact exports from verified simulator suites. They are **not**
complete inputs to `analyze-suite`, `diagnose-suite`, interval fitting or evaluation:
raw databases/counts, full predictions, original receipts and circuit exports are omitted.
`audit_receipts.json` records hashes of the original core artifacts, and
`export_receipt.json` records hashes of the copied reports. Reproduce the full suites
using the [protocol](../../../docs/exposure_protocol.md).

| Folder | Role | Cases | Seed clusters | Policies |
|---|---|---:|---:|---:|
| `h2-development/` | Development, not final evidence | 4 | 5 | 8 |
| `ising-development/` | Secondary development transfer check | 2 | 5 | 8 |
| `h2-calibration/` | Independent interval calibration, not final test evidence | 4 | 20 | 8 |
| `h2-held-out/` | Frozen fresh-seed test and calibrated interval evaluation | 4 | 20 | 8 |

The held-out primary contrast is **−0.00710821**, with paired seed-cluster 95% interval
**[−0.00909278, −0.00505381]**. Component-matched racing's mean regret is 0.00360119,
compared with blind reuse's 0.0107094 (66.4% lower); 18 seeds favored matching and 2 favored
blind reuse. The GP, fresh, global and uniform controls are not separated on mean regret.
Joint calibrated coverage is 19/20 seed clusters, with mean full-bank interval width 0.20944.
Read [the full interpretation, controls, and widths](../../../docs/exposure_results.md).

The separately downloadable `DriftQAS_v04_raw_evidence.zip` preserves complete data for
190 verified paired episodes plus 80 failed-calibration episodes for audit only. Its
[catalogue and SHA256](evidence_bundle.json) record the exact archive. Raw data, original
receipts, banks and QASM are included; source code remains in this repository.

The H2 development primary difference was −0.0103877 (circuit-aware racing minus blind
racing reuse). The Ising difference was +0.000215842, with no true winner-rank reversals.
All cases and controls are retained. These findings do not establish general superiority.

`frozen_protocol_v2.json` binds the H2 study's source, environment, cases, budgets, policies,
primary estimand and 5/20/20 disjoint development/calibration/held-out seed partitions.
It was committed before the primary held-out run. Its source digest is
recorded in that artifact.

The original `frozen_protocol.json` is retained for the first calibration attempt, whose
80 computational episodes finished but whose final verification failed on incidental
temporary files incorrectly included in a seal. Canonical artifact hashes and database/
JSONL parity remained valid. A regression-tested explicit canonical-artifact list fixed
sealing; the calibration study was rerun from scratch under v2 before primary held-out
execution. No policy settings or seeds changed. See [the failure record](calibration_failure.md).

The development suites preceded the freeze. Between development and the freeze, only
decision-rule wording for uniform racing and the standalone summary's claim wording were
corrected in the package; controller behavior and experiment settings did not change.
Their manifests retain the actual earlier source digest. The v2 source adds only the
artifact-sealing fix to that original freeze; it does not change the controller. Later
changes to tests, CI, export tooling and documentation do not alter frozen package source.

Python 3.12.14 and tested scientific dependencies were used with BLAS/OpenMP thread
counts of one. Timing is machine-dependent, not a hardware-speedup claim. The checked-in
freeze requires exact recorded versions, including the Python patch version; to run on
a different environment, create your own new freeze and use new output directories.

Results remain specific to frozen, ideal-trained libraries under synthetic CX-only noise.
The calibration output is posthoc: it never adjusts acquisition or stopping. Any reported
coverage must be read alongside interval width and the limited number of seed clusters.

`interval_calibration.json` was fitted on the verified replacement calibration suite before
primary held-out execution. Its ID is
`a6704be0324a78626cc7e96e57b1df9300d4c0371143ef3b746c17737d262ce2`.
Circuit-aware racing's temperature is about 2.193; blind racing reuse needs about 10.083.
These are fixed posthoc interval multipliers, not changed policy settings. Calibration
partition performance is not final held-out evidence.

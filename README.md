# DriftQAS

**Circuit-aware evidence reuse for budgeted quantum circuit selection under simulated drift.**

DriftQAS asks which quantum-circuit results remain useful after execution conditions change,
and which experiments are worth repeating. This repository provides a runnable simulation
prototype with explicit measurement costs and independent scoring.

## Current implementation

- Two-qubit H₂ and 2–6 qubit open-boundary Ising Hamiltonians.
- Seeded, bounded circuit libraries with ideal parameter training and physical compilation.
- Explicit grouped Pauli measurements using Qiskit Aer, including within-group covariance.
- Local CX depolarizing noise with stable, abrupt, gradual, and recurring profiles.
- Six allocation policies: random, restart, unchanged reuse, global forgetting,
  periodic refresh, and DriftQAS; three isolated DriftQAS ablations.
- An ideal-energy prior plus a Gaussian-process model of noisy residuals.
- Circuit-specific discounting and a transparent refresh/promotion policy.
- Protected confirmation budgets, reproducible measurement streams, SQLite/JSONL records,
  CSV results, plots, and OpenQASM 3 circuit exports.
- Declared repeated-seed suites, separate development/held-out seeds, paired bootstrap
  intervals, empirical coverage diagnostics, and verified episode-level resumption.
- Component-matched racing with fresh/global/blind/uniform controls and an ideal-only baseline.
- Stratified footprint anchors, offline exposure/ranking checks, full-bank prediction locks,
  and frozen development/calibration/held-out evaluation with posthoc interval scales.

**Scope:** candidates and parameters are frozen before the online comparison. This is
finite-library selection under synthetic entangler noise. Preparation cost is reported
separately. Dynamic architecture generation, noisy parameter training inside the online
budget, joint evaluation-source acquisition, and physical QPU execution are future milestones.
The GP uncertainty and relevance weights are heuristics, not proven calibrated guarantees.
The racing bounds are also heuristic. Posthoc calibrated intervals never affect the controller;
their assumptions and width penalties are reported separately.

## Quick start

Python **3.12** is the tested environment. No GPU, cloud account, or quantum hardware is
needed for these examples.

### Windows PowerShell

```powershell
git clone https://github.com/kowshikdev/DriftQAS.git
cd DriftQAS
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m driftqas run --config configs/smoke.yaml
```

Calling the virtual environment's Python directly avoids PowerShell activation-policy issues.

### Linux / macOS

```bash
git clone https://github.com/kowshikdev/DriftQAS.git
cd DriftQAS
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-tested.txt
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m driftqas run --config configs/smoke.yaml
```

The tested scientific and development package versions are pinned in
[`requirements-tested.txt`](requirements-tested.txt). This pins direct dependencies,
not every platform-dependent transitive dependency. `pyproject.toml` declares supported
ranges; each run records the resolved scientific package versions and source digest.

## Examples

```bash
# H2: 6 candidates, 3 calibration epochs, 3 policies
python -m driftqas run --config configs/smoke.yaml --output results/h2-example

# Four-qubit Ising: 12 candidates, 4 epochs, all 6 policies
python -m driftqas compare --config configs/ising.yaml --output results/ising-example

# Recreate the CSV and plot from a completed run
python -m driftqas analyze --run-dir results/ising-example
```

Run and compare both execute the policy list declared in the YAML file. An existing nonempty
output directory is refused, so choose a new path for another run. `results/` is ignored by Git.

| Output | Contents |
|---|---|
| `manifest.json` | Configuration, task/reference, package versions, source digest, run status |
| `candidates.json` | Architecture, trained angles, ideal cost, compilation, native footprint |
| `experiments.sqlite` / `experiments.jsonl` | Requests, decisions, raw counts, uncertainty, costs, locked choices |
| `summary.json` | Independent confirmation and offline audit outcomes |
| `comparison.csv` / `comparison.png` | Policy results and a development comparison figure |
| `circuits/<policy>/epoch_<n>.qasm` | Compiled recommended circuit at each epoch |

Small checked-in example results are in [`examples/development`](examples/development).
See [`docs/development_results.md`](docs/development_results.md) for their interpretation.
They are single-seed development runs, not evidence of research superiority.

## Repeated-seed benchmarks

```bash
# Read-only validation and resource bounds for the proposed full study
python -m driftqas suite --config configs/benchmark_ising.yaml --plan

# Small workflow validation: 2 cases, 3 seeds, 9 policies (intervals withheld)
python -m driftqas suite --config configs/suite_smoke.yaml --output results/suite-smoke

# Small Ising development pilot: 2 cases, 5 seeds, 9 policies
python -m driftqas suite --config configs/suite_pilot.yaml --output results/ising-pilot

# Verify completed episodes and retry unfinished episodes in a new attempt directory
python -m driftqas suite --config configs/suite_pilot.yaml --output results/ising-pilot --resume

# Rebuild reports from a complete, verified suite without simulation
python -m driftqas analyze-suite --suite-dir results/ising-pilot
```

Each suite freezes its case/seed/policy matrix, primary comparison, code digest, and resolved
versions before execution. The primary contrast is DriftQAS minus reuse in mean selection
regret; negative differences favor DriftQAS. Epochs and cases are averaged within a seed
before seed clusters are bootstrapped. Missing pairs and damaged artifacts block reporting.
Intervals are withheld below five seeds; five is still a small development sample.

`report.md`, `episodes.csv`, `policy_summary.csv`, `paired_comparisons.csv`, and
`suite_summary.json` contain the comparison and coverage diagnostics. Full run artifacts
remain in `episodes/<case>/seed_<n>/attempt_<n>/`. Completed attempts are sealed with SHA256
checksums. Resume requires the exact declaration, source, and dependency versions; failed
attempts are preserved and rerun from the beginning. This does not resume an individual
episode mid-epoch. See [the benchmark protocol](docs/benchmark_protocol.md).

The larger `benchmark_ising.yaml` is a protocol candidate, not a completed or powered study.
Its default development partition has 80 paired episodes, 720 policy episodes, and an upper
bound of 53,084,160 online simulator shots. Inspect `--plan` before running it. Freeze choices
after development and use a new output directory for `split: held_out`; labels alone cannot
prove that seeds were never inspected.

Verified smoke and five-seed pilot exports are in [examples/benchmarks](examples/benchmarks).
DriftQAS tied reuse on the pilot's primary metric; the coverage checks also expose limitations
of the current heuristic uncertainty. See [the interpretation](docs/development_results.md).

## Exposure and uncertainty milestone (v0.4)

The [v0.4 protocol](docs/exposure_protocol.md) adds same-family racing controls, structurally
diverse banks, and read-only exposure/ranking diagnostics. It freezes every experimental
choice before separate calibration and held-out partitions. Interval calibration is posthoc;
it never changes the controller's recommendations or stopping rule.

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m driftqas suite --config configs/exposure_h2.yaml --plan
python -m driftqas suite --config configs/exposure_h2.yaml --output results/exposure-dev
python -m driftqas diagnose-suite --suite-dir results/exposure-dev
python -m driftqas freeze --config configs/exposure_h2.yaml --output results/frozen.json
```

Use the full calibration/test command sequence in the protocol. Those runs require the
matching freeze and disjoint seed partitions; changing source, versions or settings is
rejected before execution. The primary contrast is circuit-aware racing minus blind racing
reuse, not a claim of beating every baseline. Stable/mild/stress cases remain in the primary
average. Coverage must be interpreted alongside interval widths and seed-level dependence.

## Budget and scoring

`low_shots` and `high_shots` mean shots **per measurement group**. `budget_per_epoch`
limits total sampled shots across all groups and all candidates. Identity terms do not need
measurements. A portion of every epoch's budget is protected for fresh final confirmation.

The candidate is locked before confirmation. Confirmation may inform a later epoch, but
cannot change the choice being scored. Offline density-matrix audits start only after every
policy has finished; they are not available to the controller.

Initial ideal training has a hard objective-call cap per candidate. Its cost is shared and
reported separately from online shots. Simulator shots are an experimental resource proxy,
not physical QPU expenditure or a guarantee of CPU savings. Measurement CPU/wall time and
overall preparation/analysis times are recorded.

The H₂ reference is the eigenvalue of the supplied reduced Hamiltonian, approximately
`-1.8572750302`, without adding a nuclear-energy offset. Do not compare it directly with
a total molecular energy using a different convention.

## Development

```bash
python -m pytest -q
ruff check .
ruff format --check .
```

CI runs checks, the H₂ smoke example, and the repeated-seed smoke suite with verified resumption
on Python 3.12. Numerical tests cover the reference,
zero-noise behavior, sampling, Pauli ordering and covariance; protocol tests cover budgets,
configuration, drift relevance, deterministic replay, and confirmation/audit isolation.
It also executes a tiny frozen calibration/held-out workflow, including interval fitting,
exposure diagnostics, calibrated coverage and verified resumption. That CI workflow is
validation, not scientific evidence.

Suite resumption skips verified completed episodes and preserves unfinished attempts before
retrying. Standalone interrupted runs preserve events but need a new directory to replay.

## Research direction

The proposed contribution connects a circuit's compiled dependence on changed components
to historical-evidence uncertainty and budgeted revalidation. Noise-aware search, continual
learning, surrogate-guided QAS, and shot allocation all have prior work. No “first”, quantum
advantage, or hardware-speedup claim is made.

- [Implementation methodology](docs/methodology.md)
- [Complete research and implementation plan](docs/project_plan.md)
- [Development result interpretation](docs/development_results.md)
- [Repeated-seed benchmark protocol and ablations](docs/benchmark_protocol.md)
- [Exposure, racing, and frozen interval-calibration protocol](docs/exposure_protocol.md)

## References

- [Qiskit Algorithms H₂/VQE example](https://qiskit-community.github.io/qiskit-algorithms/tutorials/01_algorithms_introduction.html)
- [IBM: building noise models](https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models)
- [QuantumNAS](https://hanlab.mit.edu/projects/quantumnas)
- [Quantum Architecture Search via Continual Reinforcement Learning](https://arxiv.org/abs/2112.05779)
- [Graph-Based Bayesian Optimization for QAS](https://arxiv.org/abs/2512.09586)

## License

Apache 2.0. See [LICENSE](LICENSE).

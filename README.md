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
  periodic refresh, and DriftQAS.
- An ideal-energy prior plus a Gaussian-process model of noisy residuals.
- Circuit-specific discounting and a transparent refresh/promotion policy.
- Protected confirmation budgets, reproducible measurement streams, SQLite/JSONL records,
  CSV results, plots, and OpenQASM 3 circuit exports.

**Scope:** candidates and parameters are frozen before the online comparison. This is
finite-library selection under synthetic entangler noise. Preparation cost is reported
separately. Dynamic architecture generation, noisy parameter training inside the online
budget, joint evaluation-source acquisition, and physical QPU execution are future milestones.
The GP uncertainty and relevance weights are heuristics, not proven calibrated guarantees.

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

Use the feature branch or PR checkout if this implementation has not been merged into `main`.
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

CI runs checks and the H₂ smoke example on Python 3.12. Numerical tests cover the reference,
zero-noise behavior, sampling, Pauli ordering and covariance; protocol tests cover budgets,
configuration, drift relevance, deterministic replay, and confirmation/audit isolation.

Interrupted runs preserve committed experiment events but automatic continuation is not
implemented yet. Use a new run directory to replay a configuration.

## Research direction

The proposed contribution connects a circuit's compiled dependence on changed components
to historical-evidence uncertainty and budgeted revalidation. Noise-aware search, continual
learning, surrogate-guided QAS, and shot allocation all have prior work. No “first”, quantum
advantage, or hardware-speedup claim is made.

- [Implementation methodology](docs/methodology.md)
- [Complete research and implementation plan](docs/project_plan.md)
- [Development result interpretation](docs/development_results.md)

## References

- [Qiskit Algorithms H₂/VQE example](https://qiskit-community.github.io/qiskit-algorithms/tutorials/01_algorithms_introduction.html)
- [IBM: building noise models](https://quantum.cloud.ibm.com/docs/en/guides/build-noise-models)
- [QuantumNAS](https://hanlab.mit.edu/projects/quantumnas)
- [Quantum Architecture Search via Continual Reinforcement Learning](https://arxiv.org/abs/2112.05779)
- [Graph-Based Bayesian Optimization for QAS](https://arxiv.org/abs/2512.09586)

## License

Apache 2.0. See [LICENSE](LICENSE).

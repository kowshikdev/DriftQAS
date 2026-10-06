# Repeated-seed evaluation protocol (v0.3)

The first prototype makes chronological, budgeted choices. This milestone makes those choices
comparable across seeds and checks whether each proposed mechanism is helping. It adds
evaluation infrastructure; it does not establish novelty, superiority, or hardware speedup.

## Declared requirements

| Requirement | Implementation |
|---|---|
| Shared task, bank, training, noise, budget and evaluator | Existing runner per case/seed; all declared policies share that episode |
| Separate development and held-out intent | Two nonempty, unique, disjoint seed sets; one declared split per suite |
| Frozen comparison and full matrix | Suite manifest, protocol digest, exact source/dependency identity written before runs |
| Stable control and changing conditions | Explicit case list; stable, abrupt, gradual and recurring are supported |
| One-component ablations | Named relevance, refresh and allocation controls below |
| No audit leakage | Predictions locked before confirmation; audits run after every policy finishes |
| Correct repeated-seed uncertainty | Paired differences, clustered by seed, with epochs/cases reduced first |
| No selective omission | Every declared case/seed/policy/epoch required before reports are written |
| Safe retry and provenance | Completed artifacts sealed; failed attempts retained; exclusive suite writer |
| Resource visibility | Read-only plan reports shot, ideal-training and offline-audit bounds |

Candidate banks are regenerated deterministically for each case/seed, not cached across cases.
Preparation remains shared across policies within an episode and reported separately. Policies
receive calibration only in chronological order. The suite manifest declares the experimental
matrix to the operator, not to the selection policy.

## Policy and ablation definitions

All policies use the same available features and GP family, except random's allocation rule.
The six original policies retain their behavior. The three new ablations each change one
control relative to DriftQAS:

| Policy | Historical relevance | Forced leader refresh | Search shots per group |
|---|---|---|---|
| `driftqas` | Circuit footprint exposure | Up to three affected, observed leaders | Staged low/high |
| `driftqas_global_relevance` | Maximum edge-error change, independent of footprint | Same affected-leader rule | Same staged rule |
| `driftqas_no_refresh` | Same circuit relevance | Disabled | Same staged rule |
| `driftqas_fixed_shots` | Same circuit relevance | Same affected-leader rule | Always `high_shots` |

Global relevance still has footprint-aware features and refresh eligibility. It isolates the
relevance formula, not all circuit information. No-refresh disables only the forced queue;
normal acquisition may still remeasure historical candidates. Fixed allocation applies to
initial seeds, refresh and subsequent search. It leaves an unaffordable remainder unused;
confirmation retains the same independently reserved allocation. Its larger seed cost is
validated before any circuit preparation. Reports include actual shots and utilization,
so identical limits are not confused with identical spending.

The existing `global_forgetting` baseline has global relevance and no forced refresh. It is
therefore distinct from `driftqas_global_relevance`. Component settings are recorded in every
episode manifest. Features, kernel, ideal preparation and confirmation rules are unchanged.

## Primary estimand and uncertainty

For policy p, case c, seed s, first average exact offline selection regret over the episode's
epochs. Compute the target-minus-comparator difference on that matched episode. Average
differences equally over all declared cases for the same seed, then average over seeds.
The primary metric includes stable and pre-change epochs; it is not a post-change-only metric.
Changing that definition requires a new declared protocol before evaluation.

The default primary target is `driftqas` and comparator is `reuse`. Negative regret differences
favor the target. Primary analysis has exactly one scope/metric/comparator combination.
Case-specific differences, final regret, shot differences, other baselines and ablations are
secondary descriptive comparisons. Their intervals are not adjusted for multiplicity.

Bootstrap seed clusters with replacement and use the 2.5th/97.5th percentiles of the resampled
mean. Epochs, shots and cases sharing the same seed are not independent replicates. A five-seed
minimum suppresses intervals for tiny workflow examples; it is a reporting safeguard, not a
power calculation or a guarantee of valid coverage. A zero-width interval can occur if all
observed paired differences agree; it does not establish universal equivalence or superiority.
No p-values or automatic significant-winner labels are generated.

The default larger study is 16 cases: two four-qubit Ising field strengths, four drift profiles,
and two shot limits. It has five development seeds and ten declared held-out seeds, six epochs,
six baselines and three ablations. This is a protocol candidate. Pilot runtime, effect scale,
variance and uncertainty behavior must inform whether the eventual frozen study needs more
seeds or additional conditions. Do not inspect held-out results and then tune against them.

Mixed Hamiltonians can have different energy scales. The macro average uses supplied raw
energy units with equal case weights; case-specific reports remain necessary for physical
interpretation. The seed partition does not isolate every kind of transfer: profiles, tasks
and hyperparameters can still be shared. A declared held-out label is not verifiable proof
that the operator never previously inspected those seeds.

## Coverage diagnostics

The mean and model SD for the locked recommendation are recorded before its independent
confirmation. Later, compare the exact current noisy audit energy with:

- locked GP mean plus/minus 1.959964 model SD;
- independent confirmation energy plus/minus 1.959964 estimated measurement SE.

Model coverage concerns the latent energy, not a future finite-shot measurement interval.
Confirmation coverage uses a normal approximation and includes grouped-term covariance in
the SE. Both are diagnostics on adaptively selected recommendations, not all bank candidates.
Zero estimated confirmation SE is reported separately; finite samples can miss rare outcomes.
Coverage averages epochs within an episode, cases within seed, and then seeds. No binomial
interval pretending correlated epochs are independent is reported. These checks do not
certify GP calibration or relevance weights.

## Completion and resumption

`suite_manifest.json` freezes the normalized declaration, every expanded episode, package
versions, Python version and complete package source digest. `suite_status.json` tracks
progress. Every completed attempt receives a receipt containing hashes of its canonical
artifacts: manifest, summary, candidate bank, both event representations, and every declared
policy/epoch QASM export. Missing circuits are rejected. Incidental transport/runtime files
are not experiment evidence and are not sealed. Checksums and database/export parity on
actual experiment artifacts remain mandatory.
Active events use a separate `experiments.live.sqlite` pager. The final `experiments.sqlite`
is published through an atomic, closed snapshot and completion is published
only after both event artifacts are closed. Database and JSONL export must agree before sealing.
The report requires all declared
pairs and validates outcome completeness, finiteness,
nonnegative uncertainties and the shot ledger before aggregating.

`--resume` requires the exact original configuration and runtime identity. It verifies all
completion receipts before running pending work, skips completed episodes and starts a new
numbered attempt for unfinished episodes. A completed but unsealed attempt can be validated
and sealed without rerunning. Failed/partial events are never erased. A completed attempt
with missing or changed artifacts is rejected rather than silently replaced.

Only one suite writer is allowed. A process killed without cleanup can leave `.suite.lock`.
Verify no writer is running before manually removing that stale lock. Do not delete episode
files to conceal unfavorable results. Mid-episode continuation is not implemented; retries
replay that entire case/seed episode. Changing source or dependencies requires a new suite
directory. `analyze-suite` can read a complete old suite without demanding the current source
match, but still verifies each episode against its frozen identity and artifact hashes.

## Files and commands

```bash
python -m driftqas suite --config configs/suite_pilot.yaml --plan
python -m driftqas suite --config configs/suite_pilot.yaml --output results/pilot
python -m driftqas suite --config configs/suite_pilot.yaml --output results/pilot --resume
python -m driftqas analyze-suite --suite-dir results/pilot
```

| File | Purpose |
|---|---|
| `suite_manifest.json` | Frozen protocol, identity, episode list and resource bounds |
| `suite_status.json` | Running/completed/failed/interrupted state and counts |
| `episodes/<case>/seed_<n>/attempt_<n>/` | Full existing runner artifacts and event ledger |
| `episodes/<case>/seed_<n>/completed.json` | Chosen completed attempt and artifact checksums |
| `episodes.csv` | One reduced row per policy/case/seed |
| `policy_summary.csv` | Case and equal-weight macro means, resource and coverage diagnostics |
| `paired_comparisons.csv` | Paired mean/final regret and shot contrasts, intervals and seed counts |
| `suite_summary.json` / `report.md` | Primary analysis, all comparisons and interpretation |

Reports are intentionally unavailable for incomplete suites. Resume to complete missing pairs
or start a separately declared protocol; this implementation does not silently drop failures.

# Exposure validation and calibrated diagnostics (v0.4)

This milestone is still **frozen-parameter, finite-library selection**. It adds a
mechanism-focused racing controller and a stronger evaluation protocol, not unrestricted
architecture generation. The earlier version labels in the original plan were aspirational;
end-to-end proposal and noisy training remain future work.

## Questions and acceptance conditions

| Question | Evidence required |
|---|---|
| Does drift create an adaptation opportunity? | Exact offline candidate score changes and genuine winner-regret reversals, by case/seed |
| Does the footprint identify unaffected evidence? | Zero exposure implies no score change within numerical tolerance under the declared CX-only model |
| Does circuit matching improve allocation? | Paired comparison to blind reuse in the same racing family; fresh/global/uniform controls retained |
| Is uncertainty trustworthy? | Locked full-bank predictions, independent calibration clusters, fresh-seed coverage **and interval widths** |
| Is evaluation leakage-safe? | Full predictions and recommendation locked before fresh confirmation; audits after every policy completes |
| Can the result be reproduced? | Frozen source/environment/configuration, complete seals, deterministic streams, and exact resume verification |

Exposure is the sum of compiled CX counts times absolute changes in their edge error,
divided by the declared drift scale. It is a structural sensitivity proxy, not a calibrated
predictor of the magnitude of energy change. Rank reversal means the previous winner has
positive current regret greater than `1e-8`; changing IDs among tied winners does not count.
Spearman associations are descriptive within a bank/transition and averaged within seed
before case reporting. Constant inputs are reported as undefined. Stable cases remain included.

## Shared candidate bank

`bank_design: random` preserves the earlier generator. `stratified` includes a full-chain
RY anchor, a product-state anchor, and, for chains with more than one edge, an RY anchor
omitting each individual edge. Remaining candidates are seeded random variations. All
policies share the same prepared bank, parameters, compilation and evaluator. Anchors are
chosen structurally before any held-out results, not by audit scores. Compiled footprints,
not template edges, govern compatibility. Distinct specifications need not be distinct
states or distinct compiled circuits. The ideal objective-call cap remains hard and reported.

Better-trained candidates and structural diversity can expose a mechanism that an
undertrained smoke bank misses. They also change the experimental population. Results
must not be presented as a direct improvement on the old smoke bank or as a proof that
larger noise always causes a ranking reversal.

## Racing family and controls

| Policy | Compatible historical observations | Allocation |
|---|---|---|
| `fresh_racing` | None from earlier epochs | Incumbent/challenger racing |
| `reuse_racing` | All, even after a hardware change | Same racing rule |
| `global_racing` | Full edge-error dictionary matches current conditions | Same racing rule |
| `driftqas_racing` | Every edge used by that circuit has exactly matching error | Same racing rule |
| `driftqas_racing_uniform` | Same circuit-matching rule | Least compatible accumulated shots |
| `ideal_only` | Ideal trained energy; no noisy search | Fresh confirmation only |

The original GP policies retain their behavior. Comparisons to them change both model and
evidence management; only within-family contrasts isolate the new compatibility rule.
`ideal_only` is a useful low-cost control, not an uncertainty-calibrated noisy-energy model.

Within the declared synthetic model, single-qubit gates, basis changes and readout are
ideal, so a circuit's channel depends only on the error rates on its used CX edges. Exact
component matching permits reuse on unaffected edges and after restoration. A product-state
candidate can remain compatible despite a CX error change. This does **not** justify reuse
on real devices with unmodeled errors, uncertain calibration, crosstalk or changed parameters.

Each racing policy first measures every candidate missing compatible evidence with low
shots. It pools compatible means with shot weights, and estimated mean variances with
squared weights. Its heuristic SE is floored at `racing_floor`. The incumbent has the
lowest pooled mean; the challenger has the lowest mean minus `racing_beta * SE` among
other candidates. Sample the larger-SE member of that pair, or stop if their heuristic
bounds separate. Uniform allocation removes that choice/stop rule and spends the available
search budget. The runner can trim a final batch to the remaining group-aligned budget.

These are estimated Gaussian racing bounds, **not anytime-valid confidence sequences or
a best-arm identification guarantee**. Selection and repeated peeking can distort nominal
coverage. The low-shot full-bank requirement is checked before execution. All policies
share budget caps and protected fresh confirmation, but can spend different amounts.
Report actual shots; identical limits are not identical spending or CPU/QPU speedups.

## Development, freeze, calibration, and test

The H2 protocol in `configs/exposure_h2.yaml` declares four cases: stable, mild abrupt,
stress abrupt and stress recurring. Stress means synthetic CX depolarizing probability
`0.12`, not a claim about a typical physical device. It uses 8 candidates, at most 120
ideal fit calls each, 4 epochs, and 2,048 sampled shots per epoch. All eight controls remain
in the report. The one primary contrast is `driftqas_racing - reuse_racing` in mean exact
selection regret, averaged over **all epochs and all cases** within seed, then over seeds.
Negative differences favor circuit matching. Other contrasts are secondary and unadjusted.

Five development seeds are for debugging and judgment, not final evidence. Twenty distinct
calibration seeds fit interval scales; twenty new held-out seeds evaluate the frozen
controller and intervals. The secondary four-qubit Ising configuration is development-only
and must not be relabeled held-out or used to claim transfer. The prior Ising pilot had
little ranking change, so H2 is the primary mechanism test for this milestone, not the
ultimate research benchmark promised in the original roadmap.

`freeze` creates a content-addressed artifact containing every partition, case, policy,
hyperparameter, primary estimand, bootstrap setting, source digest, package versions,
Python version and thread environment. Only the selected split can differ on a subsequent
run. Calibration and held-out execution for this three-partition study require `--frozen`;
mismatches fail before output creation or simulation. Existing two-partition suites remain
supported. Hashes are consistency checks, not trusted timestamps or proof the operator
never previously inspected a seed. Commit the freeze before testing for an auditable record.

The controller receives neither the seed partition label nor future calibrations/audits.
Calibration is **posthoc interval analysis only**: it does not alter acquisition, stopping,
recommendations, means or the model SD stored during execution. There is no calibrated-online
racing claim. If code or experimental settings change, create a new freeze and rerun the
calibration/test study; do not overwrite the old results or tune against held-out outcomes.

## Interval construction and limitations

At each lock, save a prediction for every bank candidate before confirmation. After the
entire episode finishes, compare those predictions to the exact noisy audit. For each
policy and calibration seed, take the maximum over **all declared cases, epochs and
candidates** of

`abs(prediction - audit) / (1.959964 * max(model_SD, 0.002))`.

For `N` calibration seed clusters, take order statistic
`ceil((N + 1) * (1 - alpha))`, with frozen `alpha = 0.05`, and clamp the resulting
temperature below at 1 (never shrink). If the rank exceeds N, fitting fails rather than
pretending there is a finite calibrated interval. At N=20 the largest score is used.
Apply that fixed per-policy temperature to the floored raw width on held-out clusters.
This full-bank maximum includes the adaptively selected candidate, rather than fitting
only to whichever candidates happened to be recommended.

Report raw Gaussian coverage, calibrated coverage, joint seed coverage and width. One
joint trial spans every case/epoch/candidate of a held-out seed for one policy. Selected
and full-bank point rates are descriptive; correlated points are not independent binomial
trials. Temperature inflation can make coverage good but intervals uselessly wide. Twenty
seed clusters are a small final simulation study, not a power or coverage certification.

The split-calibration rank argument needs exchangeable independent seed clusters under
the identical frozen protocol. Listed deterministic PRNG seeds do not themselves prove
that assumption. No distribution-free validity is asserted for arbitrary changing hardware,
distribution shift, uncertain/noisy calibration, or simultaneous coverage across all policies.
Relevant primary references: [Conformal prediction beyond exchangeability](https://arxiv.org/abs/2202.13415),
[Conformal prediction under covariate shift](https://arxiv.org/abs/1904.06019), and
[Adaptive conformal inference under distribution shift](https://arxiv.org/abs/2106.00170).
The weighted/adaptive algorithms in those papers are **not** implemented here.

## Reproduce

Use the tested dependencies. Keep thread settings consistent with the freeze:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m driftqas suite --config configs/exposure_h2.yaml --plan
python -m driftqas suite --config configs/exposure_h2.yaml --output results/h2-dev
python -m driftqas diagnose-suite --suite-dir results/h2-dev

python -m driftqas freeze --config configs/exposure_h2.yaml --output results/frozen.json
python -m driftqas suite --config configs/exposure_h2.yaml --split calibration \
  --frozen results/frozen.json --output results/h2-calibration
python -m driftqas calibrate --suite-dir results/h2-calibration \
  --output results/interval-calibration.json
python -m driftqas suite --config configs/exposure_h2.yaml --split held_out \
  --frozen results/frozen.json --output results/h2-held-out
python -m driftqas diagnose-suite --suite-dir results/h2-held-out
python -m driftqas evaluate-calibration --suite-dir results/h2-held-out \
  --calibration results/interval-calibration.json
```

Never overwrite a freeze or calibration artifact. Suite resumption still requires exact
source/environment/configuration and verified database/export parity plus artifact seals.
Diagnostic and interval reports reject incomplete full-bank prediction/audit grids and
invalid chronology. `diagnose-suite` requires v0.4 full-bank snapshots; old suites remain
readable using `analyze-suite`.

Seals cover the five canonical core artifacts and every declared policy/epoch QASM, not
incidental environment-created files. A first calibration attempt exposed this distinction;
[its failure record](../examples/benchmarks/v04/calibration_failure.md) is retained. Its
replacement freeze changes sealing only, not the controller or experimental choices.

New exports: `exposure_pairs.csv`, `exposure_episodes.csv`, `prediction_diagnostics.csv`,
`diagnostics_summary.json`, `calibrated_seed_coverage.csv`, `calibrated_policy_summary.csv`
and `calibrated_summary.json`. These are derived reports, not replacements for complete
event logs, receipts and manifests.

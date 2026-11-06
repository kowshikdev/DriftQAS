# locality-ising-v05 (held_out)

Complete paired episodes: **60**; independent seed clusters: **20**.
Protocol: `261a7cd4426f3974f510832eb7912b15219ca5d39c2edd79054888187d4c3d35`.

Primary contrast: **driftqas_racing minus global_racing**, mean selection regret.
Mean difference: **-0.00601922**; 95% interval: [-0.0241084, 0.012322].
Negative differences favor the target. This development or declared held-out report does not itself establish superiority.

## Declared cases

| Case | Task | Profile | Epochs | Shot limit / epoch |
|---|---|---|---:|---:|
| stable | Ising 4q, field 1.5 | stable | 4 | 1024 |
| abrupt-end | Ising 4q, field 1.5 | abrupt | 4 | 1024 |
| abrupt-central | Ising 4q, field 1.5 | abrupt | 4 | 1024 |

## Paired mean-regret contrasts

| Scope | Comparator | Difference | 95% interval | Better / tie / worse seeds |
|---|---|---:|---|---|
| all_cases | reuse | 0.0856384 | [0.069526, 0.102333] | 0 / 0 / 20 |
| all_cases | driftqas | 0.0820933 | [0.062182, 0.100794] | 1 / 0 / 19 |
| all_cases | ideal_only | -0.0619882 | [-0.117716, -0.00718729] | 13 / 0 / 7 |
| all_cases | fresh_racing | -0.0318573 | [-0.0525657, -0.0106454] | 16 / 0 / 4 |
| all_cases | reuse_racing | -0.0165718 | [-0.0275813, -0.00626879] | 13 / 2 / 5 |
| all_cases | global_racing | -0.00601922 | [-0.0241084, 0.012322] | 10 / 2 / 8 |
| all_cases | driftqas_racing_uniform | 0.00639302 | [-0.0100809, 0.0233477] | 10 / 0 / 10 |
| stable | reuse | 0.0689475 | [0.0444386, 0.094728] | 0 / 3 / 17 |
| stable | driftqas | 0.0689475 | [0.0442873, 0.0950824] | 0 / 3 / 17 |
| stable | ideal_only | 0.0578677 | [0.0300621, 0.0871063] | 2 / 3 / 15 |
| stable | fresh_racing | -0.030659 | [-0.0575623, -0.00419031] | 14 / 0 / 6 |
| stable | reuse_racing | 0 | [0, 0] | 0 / 20 / 0 |
| stable | global_racing | 0 | [0, 0] | 0 / 20 / 0 |
| stable | driftqas_racing_uniform | 0.0140163 | [-0.00221487, 0.0297667] | 4 / 5 / 11 |
| abrupt-end | reuse | 0.0924365 | [0.0569915, 0.128988] | 1 / 1 / 18 |
| abrupt-end | driftqas | 0.0946969 | [0.0559477, 0.134358] | 2 / 1 / 17 |
| abrupt-end | ideal_only | -0.141171 | [-0.237201, -0.0470289] | 15 / 0 / 5 |
| abrupt-end | fresh_racing | -0.0185051 | [-0.0617984, 0.02323] | 12 / 0 / 8 |
| abrupt-end | reuse_racing | -0.0214597 | [-0.0469057, 0.00301562] | 8 / 5 / 7 |
| abrupt-end | global_racing | 0.000445358 | [-0.0434698, 0.0405631] | 7 / 5 / 8 |
| abrupt-end | driftqas_racing_uniform | 0.00251553 | [-0.0279067, 0.0341455] | 10 / 3 / 7 |
| abrupt-central | reuse | 0.0955312 | [0.0633223, 0.130578] | 0 / 1 / 19 |
| abrupt-central | driftqas | 0.0826353 | [0.0433756, 0.122186] | 2 / 1 / 17 |
| abrupt-central | ideal_only | -0.102661 | [-0.172337, -0.0344354] | 15 / 0 / 5 |
| abrupt-central | fresh_racing | -0.0464077 | [-0.0839286, -0.00834126] | 16 / 0 / 4 |
| abrupt-central | reuse_racing | -0.0282556 | [-0.0575049, -0.0019332] | 9 / 7 / 4 |
| abrupt-central | global_racing | -0.018503 | [-0.0496096, 0.0108035] | 6 / 10 / 4 |
| abrupt-central | driftqas_racing_uniform | 0.00264719 | [-0.0226365, 0.0240428] | 8 / 2 / 10 |

## Coverage and resource diagnostics (all cases)

| Policy | Mean regret | Budget used | Confirmation coverage | Model coverage | Zero confirmation SE |
|---|---:|---:|---:|---:|---:|
| reuse | 0.015763 | 96.5% | 94.6% | 84.6% | 0.0% |
| driftqas | 0.0193082 | 96.8% | 94.2% | 82.9% | 0.0% |
| ideal_only | 0.16339 | 19.9% | 95.4% | 66.7% | 0.0% |
| fresh_racing | 0.133259 | 94.9% | 97.5% | 73.8% | 0.0% |
| reuse_racing | 0.117973 | 94.9% | 95.8% | 63.3% | 0.0% |
| global_racing | 0.107421 | 94.9% | 96.2% | 80.4% | 0.0% |
| driftqas_racing | 0.101401 | 95.7% | 96.7% | 79.6% | 0.0% |
| driftqas_racing_uniform | 0.0950084 | 95.7% | 95.0% | 77.1% | 0.0% |

## Interpretation

- Differences are target minus comparator; negative regret differences favor target.
- Primary metric averages all declared epochs, then cases equally within seed, then seeds.
- Independent seed clusters are the resampling units, not shots, epochs, policies, or cases.
- 95% percentile intervals are withheld below 5 seeds. This threshold does not guarantee sufficient power or accurate bootstrap coverage.
- One contrast is primary. Other intervals are descriptive and unadjusted for multiplicity.
- Coverage uses locked mean +/- 1.959964 model SD or independent confirmation SE against the later exact noisy audit. It is a diagnostic, not a calibration guarantee.
- Coverage is averaged by episode and seed; correlated epochs are not independent coverage trials.
- A suite with mixed Hamiltonians reports an equal-weight raw-energy macro average. Use per-case results for physical interpretation.
- A held_out label records declared intent; it cannot prove seeds were never inspected.
- Frozen library, frozen parameters, synthetic CX noise; no hardware or superiority claim.

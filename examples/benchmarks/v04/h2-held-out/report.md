# exposure-h2-v04 (held_out)

Complete paired episodes: **80**; independent seed clusters: **20**.
Protocol: `424b12c357430b32fbde3d6b24ea7d1ba7a53bdbf1ea36765099a99135090980`.

Primary contrast: **driftqas_racing minus reuse_racing**, mean selection regret.
Mean difference: **-0.00710821**; 95% interval: [-0.00909278, -0.00505381].
Negative differences favor the target. This development or declared held-out report does not itself establish superiority.

## Declared cases

| Case | Task | Profile | Epochs | Shot limit / epoch |
|---|---|---|---:|---:|
| stable | H2 | stable | 4 | 2048 |
| abrupt-mild | H2 | abrupt | 4 | 2048 |
| abrupt-stress | H2 | abrupt | 4 | 2048 |
| recurring-stress | H2 | recurring | 4 | 2048 |

## Paired mean-regret contrasts

| Scope | Comparator | Difference | 95% interval | Better / tie / worse seeds |
|---|---|---:|---|---|
| all_cases | reuse | 0.000521401 | [-0.000596898, 0.00165457] | 8 / 0 / 12 |
| all_cases | driftqas | 0.000696558 | [-0.00026074, 0.00170577] | 8 / 0 / 12 |
| all_cases | ideal_only | -0.0133153 | [-0.0160033, -0.0115069] | 20 / 0 / 0 |
| all_cases | fresh_racing | -0.000711376 | [-0.00173308, 0.000270781] | 9 / 0 / 11 |
| all_cases | reuse_racing | -0.00710821 | [-0.00909278, -0.00505381] | 18 / 0 / 2 |
| all_cases | global_racing | -0.000236985 | [-0.000944302, 0.000385708] | 10 / 3 / 7 |
| all_cases | driftqas_racing_uniform | -0.000334425 | [-0.00129801, 0.00066753] | 12 / 0 / 8 |
| stable | reuse | 0.00118111 | [-0.000349718, 0.00294289] | 10 / 0 / 10 |
| stable | driftqas | 0.00118111 | [-0.000413268, 0.0029553] | 10 / 0 / 10 |
| stable | ideal_only | 0.00304136 | [0.00138249, 0.00489667] | 1 / 2 / 17 |
| stable | fresh_racing | -0.00127012 | [-0.00329629, 0.000616516] | 13 / 0 / 7 |
| stable | reuse_racing | 0 | [0, 0] | 0 / 20 / 0 |
| stable | global_racing | 0 | [0, 0] | 0 / 20 / 0 |
| stable | driftqas_racing_uniform | -0.000152203 | [-0.00148482, 0.00133779] | 7 / 3 / 10 |
| abrupt-mild | reuse | 0.000520503 | [-0.000940197, 0.00206501] | 6 / 0 / 14 |
| abrupt-mild | driftqas | -0.000786612 | [-0.00360184, 0.00149658] | 6 / 0 / 14 |
| abrupt-mild | ideal_only | -0.000424502 | [-0.00234095, 0.00135967] | 9 / 0 / 11 |
| abrupt-mild | fresh_racing | -0.000920092 | [-0.00343207, 0.00159909] | 13 / 0 / 7 |
| abrupt-mild | reuse_racing | -0.000898227 | [-0.00281985, 0.000982061] | 11 / 3 / 6 |
| abrupt-mild | global_racing | 0.000458217 | [-0.00164805, 0.00219921] | 4 / 8 / 8 |
| abrupt-mild | driftqas_racing_uniform | -0.00069151 | [-0.00344989, 0.00187061] | 10 / 1 / 9 |
| abrupt-stress | reuse | 0.000257521 | [-0.000731613, 0.00129984] | 7 / 4 / 9 |
| abrupt-stress | driftqas | 0.000257521 | [-0.000706294, 0.00128989] | 7 / 4 / 9 |
| abrupt-stress | ideal_only | -0.0390164 | [-0.0440872, -0.0361245] | 20 / 0 / 0 |
| abrupt-stress | fresh_racing | -0.00133947 | [-0.00340187, -6.21032e-05] | 7 / 10 / 3 |
| abrupt-stress | reuse_racing | -0.016503 | [-0.0223842, -0.0107079] | 14 / 6 / 0 |
| abrupt-stress | global_racing | -1.62957e-07 | [-4.21413e-07, -5.27217e-16] | 3 / 17 / 0 |
| abrupt-stress | driftqas_racing_uniform | 8.47795e-05 | [-0.000745102, 0.000982018] | 6 / 7 / 7 |
| recurring-stress | reuse | 0.000126474 | [-0.00339099, 0.0034441] | 7 / 1 / 12 |
| recurring-stress | driftqas | 0.00213422 | [0.000503359, 0.00453539] | 5 / 1 / 14 |
| recurring-stress | ideal_only | -0.0168618 | [-0.0204135, -0.0137036] | 19 / 0 / 1 |
| recurring-stress | fresh_racing | 0.00068418 | [-0.00103768, 0.00305034] | 8 / 1 / 11 |
| recurring-stress | reuse_racing | -0.0110316 | [-0.0152445, -0.00681512] | 17 / 0 / 3 |
| recurring-stress | global_racing | -0.00140599 | [-0.00374627, 0.000245617] | 7 / 9 / 4 |
| recurring-stress | driftqas_racing_uniform | -0.000578765 | [-0.00306835, 0.00100761] | 7 / 1 / 12 |

## Coverage and resource diagnostics (all cases)

| Policy | Mean regret | Budget used | Confirmation coverage | Model coverage | Zero confirmation SE |
|---|---:|---:|---:|---:|---:|
| reuse | 0.00307979 | 98.4% | 97.2% | 46.6% | 0.0% |
| driftqas | 0.00290463 | 98.4% | 96.6% | 47.8% | 0.0% |
| ideal_only | 0.0169165 | 19.9% | 96.2% | 100.0% | 0.0% |
| fresh_racing | 0.00431256 | 99.9% | 95.3% | 60.0% | 0.0% |
| reuse_racing | 0.0107094 | 99.9% | 95.9% | 61.9% | 0.0% |
| global_racing | 0.00383817 | 99.8% | 95.9% | 70.3% | 0.0% |
| driftqas_racing | 0.00360119 | 99.4% | 95.9% | 71.6% | 0.0% |
| driftqas_racing_uniform | 0.00393561 | 99.9% | 95.9% | 76.9% | 0.0% |

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

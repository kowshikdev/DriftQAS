# exposure-h2-v04 (calibration)

Complete paired episodes: **80**; independent seed clusters: **20**.
Protocol: `c1db893564dff694eb935d216785d7d17444dde266ca25a33d9b6a52c5173b13`.

Primary contrast: **driftqas_racing minus reuse_racing**, mean selection regret.
Mean difference: **-0.00698601**; 95% interval: [-0.00900884, -0.0050014].
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
| all_cases | reuse | 0.000314542 | [-0.0006753, 0.00103431] | 5 / 0 / 15 |
| all_cases | driftqas | 0.000792439 | [0.000282735, 0.00130806] | 5 / 0 / 15 |
| all_cases | ideal_only | -0.0134693 | [-0.016034, -0.0118129] | 20 / 0 / 0 |
| all_cases | fresh_racing | -0.00125137 | [-0.00228704, -0.000263409] | 13 / 0 / 7 |
| all_cases | reuse_racing | -0.00698601 | [-0.00900884, -0.0050014] | 19 / 0 / 1 |
| all_cases | global_racing | 0.00024405 | [-0.000191697, 0.000725806] | 6 / 3 / 11 |
| all_cases | driftqas_racing_uniform | 0.000243067 | [-0.000781998, 0.00119398] | 10 / 0 / 10 |
| stable | reuse | 0.000984806 | [5.14502e-05, 0.00189928] | 5 / 1 / 14 |
| stable | driftqas | 0.000984806 | [2.35009e-05, 0.00189656] | 5 / 1 / 14 |
| stable | ideal_only | 0.00264118 | [0.00164136, 0.00370082] | 0 / 1 / 19 |
| stable | fresh_racing | -0.00100821 | [-0.00228084, 0.000102094] | 12 / 0 / 8 |
| stable | reuse_racing | 0 | [0, 0] | 0 / 20 / 0 |
| stable | global_racing | 0 | [0, 0] | 0 / 20 / 0 |
| stable | driftqas_racing_uniform | 0.000692475 | [-0.000170218, 0.00158583] | 5 / 1 / 14 |
| abrupt-mild | reuse | -0.000343437 | [-0.00242609, 0.00180385] | 11 / 0 / 9 |
| abrupt-mild | driftqas | 0.000553441 | [-0.00168124, 0.00286796] | 9 / 0 / 11 |
| abrupt-mild | ideal_only | -0.000622278 | [-0.0028626, 0.0013942] | 11 / 0 / 9 |
| abrupt-mild | fresh_racing | -0.000730998 | [-0.00316937, 0.00157076] | 10 / 0 / 10 |
| abrupt-mild | reuse_racing | -0.00316383 | [-0.00762883, 0.000525111] | 11 / 3 / 6 |
| abrupt-mild | global_racing | 0.000932833 | [-0.000650869, 0.00276048] | 5 / 7 / 8 |
| abrupt-mild | driftqas_racing_uniform | 0.00217882 | [0.000229891, 0.00438901] | 7 / 2 / 11 |
| abrupt-stress | reuse | -5.82187e-05 | [-0.00242576, 0.00159473] | 6 / 3 / 11 |
| abrupt-stress | driftqas | 0.000895289 | [0.000117322, 0.00174289] | 6 / 3 / 11 |
| abrupt-stress | ideal_only | -0.0375196 | [-0.0430257, -0.0335183] | 20 / 0 / 0 |
| abrupt-stress | fresh_racing | -0.00134062 | [-0.00461068, 0.00116518] | 8 / 2 / 10 |
| abrupt-stress | reuse_racing | -0.0125173 | [-0.0174924, -0.00764085] | 13 / 7 / 0 |
| abrupt-stress | global_racing | 2.6921e-07 | [-1.21981e-10, 7.79402e-07] | 1 / 17 / 2 |
| abrupt-stress | driftqas_racing_uniform | -0.00119559 | [-0.00403318, 0.000964929] | 5 / 7 / 8 |
| recurring-stress | reuse | 0.000675019 | [-0.000509744, 0.00189641] | 7 / 1 / 12 |
| recurring-stress | driftqas | 0.000736218 | [-0.000401558, 0.00196037] | 6 / 2 / 12 |
| recurring-stress | ideal_only | -0.0183766 | [-0.0212895, -0.0163729] | 20 / 0 / 0 |
| recurring-stress | fresh_racing | -0.00192564 | [-0.00525987, 0.000644142] | 10 / 1 / 9 |
| recurring-stress | reuse_racing | -0.0122629 | [-0.0182479, -0.00676119] | 15 / 1 / 4 |
| recurring-stress | global_racing | 4.30964e-05 | [-0.000375779, 0.000561021] | 3 / 13 / 4 |
| recurring-stress | driftqas_racing_uniform | -0.000703446 | [-0.002942, 0.000831154] | 8 / 5 / 7 |

## Coverage and resource diagnostics (all cases)

| Policy | Mean regret | Budget used | Confirmation coverage | Model coverage | Zero confirmation SE |
|---|---:|---:|---:|---:|---:|
| reuse | 0.00313266 | 98.4% | 91.9% | 45.3% | 0.0% |
| driftqas | 0.00265476 | 98.4% | 92.5% | 48.8% | 0.0% |
| ideal_only | 0.0169165 | 19.9% | 91.9% | 100.0% | 0.0% |
| fresh_racing | 0.00469856 | 100.0% | 92.5% | 67.2% | 0.0% |
| reuse_racing | 0.0104332 | 100.0% | 92.2% | 64.7% | 0.0% |
| global_racing | 0.00320315 | 99.6% | 90.6% | 73.8% | 0.0% |
| driftqas_racing | 0.0034472 | 99.6% | 90.9% | 74.1% | 0.0% |
| driftqas_racing_uniform | 0.00320413 | 99.9% | 94.7% | 80.9% | 0.0% |

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

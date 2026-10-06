# exposure-h2-v04 (development)

Complete paired episodes: **20**; independent seed clusters: **5**.
Protocol: `224e2735393e0044bdece13588934faa684c72f7df50528ef6a217f7228a2f34`.

Primary contrast: **driftqas_racing minus reuse_racing**, mean selection regret.
Mean difference: **-0.0103877**; 95% interval: [-0.0138824, -0.0068929].
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
| all_cases | reuse | -0.00091398 | [-0.0025059, 0.000447313] | 3 / 0 / 2 |
| all_cases | driftqas | -0.00091398 | [-0.00247463, 0.000447313] | 3 / 0 / 2 |
| all_cases | ideal_only | -0.0142178 | [-0.014844, -0.0135141] | 5 / 0 / 0 |
| all_cases | fresh_racing | -0.00603956 | [-0.0104088, -0.0023202] | 5 / 0 / 0 |
| all_cases | reuse_racing | -0.0103877 | [-0.0138824, -0.0068929] | 5 / 0 / 0 |
| all_cases | global_racing | -0.00163942 | [-0.0038415, -2.28031e-06] | 3 / 2 / 0 |
| all_cases | driftqas_racing_uniform | -1.75079e-05 | [-0.000609503, 0.000574487] | 3 / 0 / 2 |
| stable | reuse | 3.64435e-05 | [-0.00102092, 0.000929722] | 1 / 0 / 4 |
| stable | driftqas | 3.64435e-05 | [-0.00102092, 0.000929722] | 1 / 0 / 4 |
| stable | ideal_only | 0.00106786 | [0.000220181, 0.00191555] | 0 / 0 / 5 |
| stable | fresh_racing | -0.000998355 | [-0.00205378, 0.000219985] | 3 / 0 / 2 |
| stable | reuse_racing | 0 | [0, 0] | 0 / 5 / 0 |
| stable | global_racing | 0 | [0, 0] | 0 / 5 / 0 |
| stable | driftqas_racing_uniform | -0.000155099 | [-0.00119519, 0.000729918] | 2 / 2 / 1 |
| abrupt-mild | reuse | -0.00257223 | [-0.00533496, 0.000215702] | 3 / 1 / 1 |
| abrupt-mild | driftqas | -0.00257223 | [-0.00533496, 0.000215702] | 3 / 1 / 1 |
| abrupt-mild | ideal_only | -0.00232366 | [-0.00296842, -0.00110578] | 4 / 0 / 1 |
| abrupt-mild | fresh_racing | -0.00257963 | [-0.0068197, 0.000690828] | 3 / 1 / 1 |
| abrupt-mild | reuse_racing | -0.00238607 | [-0.00305005, -0.00113967] | 4 / 0 / 1 |
| abrupt-mild | global_racing | -0.00273128 | [-0.00701101, 6.26578e-06] | 2 / 2 / 1 |
| abrupt-mild | driftqas_racing_uniform | 0.000392321 | [-0.00158799, 0.00237263] | 2 / 0 / 3 |
| abrupt-stress | reuse | -0.00138834 | [-0.00281264, -0.000203854] | 3 / 2 / 0 |
| abrupt-stress | driftqas | -0.00138834 | [-0.00281264, -0.000203854] | 3 / 2 / 0 |
| abrupt-stress | ideal_only | -0.0381047 | [-0.0381406, -0.0380369] | 5 / 0 / 0 |
| abrupt-stress | fresh_racing | -0.012324 | [-0.0289488, 2.88726e-05] | 3 / 1 / 1 |
| abrupt-stress | reuse_racing | -0.0152667 | [-0.0191017, -0.00762812] | 4 / 1 / 0 |
| abrupt-stress | global_racing | 3.13289e-06 | [-6.52811e-15, 9.39868e-06] | 0 / 4 / 1 |
| abrupt-stress | driftqas_racing_uniform | -0.000199143 | [-0.000600658, 3.22964e-06] | 1 / 3 / 1 |
| recurring-stress | reuse | 0.000268205 | [-0.00120571, 0.00197955] | 1 / 2 / 2 |
| recurring-stress | driftqas | 0.000268205 | [-0.00120571, 0.00197955] | 1 / 2 / 2 |
| recurring-stress | ideal_only | -0.0175108 | [-0.0188228, -0.0162586] | 5 / 0 / 0 |
| recurring-stress | fresh_racing | -0.00825621 | [-0.0157117, -0.000800711] | 3 / 1 / 1 |
| recurring-stress | reuse_racing | -0.0238978 | [-0.0355165, -0.0114703] | 5 / 0 / 0 |
| recurring-stress | global_racing | -0.00382955 | [-0.0114579, 0] | 2 / 3 / 0 |
| recurring-stress | driftqas_racing_uniform | -0.000108111 | [-0.00111631, 0.000667001] | 1 / 2 / 2 |

## Coverage and resource diagnostics (all cases)

| Policy | Mean regret | Budget used | Confirmation coverage | Model coverage | Zero confirmation SE |
|---|---:|---:|---:|---:|---:|
| reuse | 0.00248499 | 98.4% | 92.5% | 46.2% | 0.0% |
| driftqas | 0.00248499 | 98.4% | 92.5% | 46.2% | 0.0% |
| ideal_only | 0.0157888 | 19.9% | 92.5% | 100.0% | 0.0% |
| fresh_racing | 0.00761057 | 99.9% | 91.2% | 53.8% | 0.0% |
| reuse_racing | 0.0119587 | 99.9% | 92.5% | 52.5% | 0.0% |
| global_racing | 0.00321043 | 99.9% | 93.8% | 63.7% | 0.0% |
| driftqas_racing | 0.00157101 | 99.8% | 93.8% | 65.0% | 0.0% |
| driftqas_racing_uniform | 0.00158852 | 100.0% | 91.2% | 70.0% | 0.0% |

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

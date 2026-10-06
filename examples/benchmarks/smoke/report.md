# suite-smoke (development)

Complete paired episodes: **6**; independent seed clusters: **3**.
Protocol: `1917ad3076b307d8c4d9199d77b468473ecfb06facc4e07fe152570be9145ac5`.

Primary contrast: **driftqas minus reuse**, mean selection regret.
Mean difference: **0**; 95% interval: unavailable (fewer than 5 seeds).
Negative differences favor the target. This development or declared held-out report does not itself establish superiority.

## Declared cases

| Case | Task | Profile | Epochs | Shot limit / epoch |
|---|---|---|---:|---:|
| h2-stable | H2 | stable | 2 | 1024 |
| h2-abrupt | H2 | abrupt | 2 | 1024 |

## Paired mean-regret contrasts

| Scope | Comparator | Difference | 95% interval | Better / tie / worse seeds |
|---|---|---:|---|---|
| all_cases | random | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| all_cases | restart | 0.000184938 | unavailable (fewer than 5 seeds) | 0 / 2 / 1 |
| all_cases | reuse | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| all_cases | global_forgetting | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| all_cases | periodic_refresh | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| all_cases | driftqas_global_relevance | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| all_cases | driftqas_no_refresh | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| all_cases | driftqas_fixed_shots | -0.000321033 | unavailable (fewer than 5 seeds) | 3 / 0 / 0 |
| h2-stable | random | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-stable | restart | 0.000369877 | unavailable (fewer than 5 seeds) | 0 / 2 / 1 |
| h2-stable | reuse | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-stable | global_forgetting | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-stable | periodic_refresh | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-stable | driftqas_global_relevance | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-stable | driftqas_no_refresh | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-stable | driftqas_fixed_shots | -0.000285193 | unavailable (fewer than 5 seeds) | 1 / 2 / 0 |
| h2-abrupt | random | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-abrupt | restart | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-abrupt | reuse | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-abrupt | global_forgetting | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-abrupt | periodic_refresh | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-abrupt | driftqas_global_relevance | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-abrupt | driftqas_no_refresh | 0 | unavailable (fewer than 5 seeds) | 0 / 3 / 0 |
| h2-abrupt | driftqas_fixed_shots | -0.000356872 | unavailable (fewer than 5 seeds) | 2 / 1 / 0 |

## Coverage and resource diagnostics (all cases)

| Policy | Mean regret | Budget used | Confirmation coverage | Model coverage | Zero confirmation SE |
|---|---:|---:|---:|---:|---:|
| random | 0.00169273 | 94.9% | 100.0% | 66.7% | 0.0% |
| restart | 0.00150779 | 94.9% | 100.0% | 75.0% | 0.0% |
| reuse | 0.00169273 | 94.9% | 100.0% | 66.7% | 0.0% |
| global_forgetting | 0.00169273 | 94.9% | 100.0% | 66.7% | 0.0% |
| periodic_refresh | 0.00169273 | 94.9% | 100.0% | 66.7% | 0.0% |
| driftqas | 0.00169273 | 94.9% | 100.0% | 66.7% | 0.0% |
| driftqas_global_relevance | 0.00169273 | 94.9% | 100.0% | 66.7% | 0.0% |
| driftqas_no_refresh | 0.00169273 | 94.9% | 100.0% | 66.7% | 0.0% |
| driftqas_fixed_shots | 0.00201377 | 94.9% | 100.0% | 75.0% | 0.0% |

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

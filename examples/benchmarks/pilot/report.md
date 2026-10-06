# ising-pilot-v1 (development)

Complete paired episodes: **10**; independent seed clusters: **5**.
Protocol: `b487372b07ec22729d494bfd784f0776886f476c67e94f646d1c95dc837b4756`.

Primary contrast: **driftqas minus reuse**, mean selection regret.
Mean difference: **0**; 95% interval: [0, 0].
Negative differences favor the target. This development or declared held-out report does not itself establish superiority.

## Declared cases

| Case | Task | Profile | Epochs | Shot limit / epoch |
|---|---|---|---:|---:|
| ising-stable | Ising 4q, field 0.5 | stable | 3 | 4096 |
| ising-abrupt | Ising 4q, field 0.5 | abrupt | 3 | 4096 |

## Paired mean-regret contrasts

| Scope | Comparator | Difference | 95% interval | Better / tie / worse seeds |
|---|---|---:|---|---|
| all_cases | random | -0.00390681 | [-0.0121072, 0.00297379] | 3 / 0 / 2 |
| all_cases | restart | -0.00821463 | [-0.018507, 0.0020777] | 3 / 1 / 1 |
| all_cases | reuse | 0 | [0, 0] | 0 / 5 / 0 |
| all_cases | global_forgetting | 0 | [0, 0] | 0 / 5 / 0 |
| all_cases | periodic_refresh | 0 | [0, 0] | 0 / 5 / 0 |
| all_cases | driftqas_global_relevance | 0 | [0, 0] | 0 / 5 / 0 |
| all_cases | driftqas_no_refresh | 0 | [0, 0] | 0 / 5 / 0 |
| all_cases | driftqas_fixed_shots | -0.00159217 | [-0.00539901, 0.00439742] | 4 / 0 / 1 |
| ising-stable | random | 0.00034441 | [-0.00560649, 0.00579632] | 2 / 1 / 2 |
| ising-stable | restart | -0.00959596 | [-0.0262227, 0.0063743] | 3 / 1 / 1 |
| ising-stable | reuse | 0 | [0, 0] | 0 / 5 / 0 |
| ising-stable | global_forgetting | 0 | [0, 0] | 0 / 5 / 0 |
| ising-stable | periodic_refresh | 0 | [0, 0] | 0 / 5 / 0 |
| ising-stable | driftqas_global_relevance | 0 | [0, 0] | 0 / 5 / 0 |
| ising-stable | driftqas_no_refresh | 0 | [0, 0] | 0 / 5 / 0 |
| ising-stable | driftqas_fixed_shots | -0.000409135 | [-0.0118941, 0.0206149] | 4 / 0 / 1 |
| ising-abrupt | random | -0.00815803 | [-0.0186689, 0.000855135] | 2 / 2 / 1 |
| ising-abrupt | restart | -0.00683331 | [-0.0211413, 0.000641351] | 1 / 3 / 1 |
| ising-abrupt | reuse | 0 | [0, 0] | 0 / 5 / 0 |
| ising-abrupt | global_forgetting | 0 | [0, 0] | 0 / 5 / 0 |
| ising-abrupt | periodic_refresh | 0 | [0, 0] | 0 / 5 / 0 |
| ising-abrupt | driftqas_global_relevance | 0 | [0, 0] | 0 / 5 / 0 |
| ising-abrupt | driftqas_no_refresh | 0 | [0, 0] | 0 / 5 / 0 |
| ising-abrupt | driftqas_fixed_shots | -0.0027752 | [-0.0121228, 0.00335875] | 1 / 1 / 3 |

## Coverage and resource diagnostics (all cases)

| Policy | Mean regret | Budget used | Confirmation coverage | Model coverage | Zero confirmation SE |
|---|---:|---:|---:|---:|---:|
| random | 0.0143005 | 98.5% | 93.3% | 93.3% | 0.0% |
| restart | 0.0186083 | 98.5% | 93.3% | 96.7% | 0.0% |
| reuse | 0.0103937 | 98.3% | 96.7% | 90.0% | 0.0% |
| global_forgetting | 0.0103937 | 98.3% | 96.7% | 93.3% | 0.0% |
| periodic_refresh | 0.0103937 | 98.3% | 96.7% | 90.0% | 0.0% |
| driftqas | 0.0103937 | 98.3% | 96.7% | 93.3% | 0.0% |
| driftqas_global_relevance | 0.0103937 | 98.3% | 96.7% | 93.3% | 0.0% |
| driftqas_no_refresh | 0.0103937 | 98.3% | 96.7% | 93.3% | 0.0% |
| driftqas_fixed_shots | 0.0119858 | 95.0% | 93.3% | 90.0% | 0.0% |

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

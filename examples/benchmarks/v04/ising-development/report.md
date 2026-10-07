# exposure-ising-development-v04 (development)

Complete paired episodes: **10**; independent seed clusters: **5**.
Protocol: `b1380f3f1f72982b1ee4ff17dd256db292aa7913d476ebadd5aabbd98efbc723`.

Primary contrast: **driftqas_racing minus reuse_racing**, mean selection regret.
Mean difference: **0.000215842**; 95% interval: [0, 0.000647527].
Negative differences favor the target. This development or declared held-out report does not itself establish superiority.

## Declared cases

| Case | Task | Profile | Epochs | Shot limit / epoch |
|---|---|---|---:|---:|
| stable | Ising 4q, field 0.5 | stable | 4 | 2048 |
| abrupt-stress | Ising 4q, field 0.5 | abrupt | 4 | 2048 |

## Paired mean-regret contrasts

| Scope | Comparator | Difference | 95% interval | Better / tie / worse seeds |
|---|---|---:|---|---|
| all_cases | reuse | -0.0104288 | [-0.02204, 0.00285345] | 3 / 0 / 2 |
| all_cases | driftqas | -0.00416827 | [-0.0125489, 0.00421234] | 3 / 0 / 2 |
| all_cases | ideal_only | -0.0437737 | [-0.110001, 0.00444555] | 3 / 0 / 2 |
| all_cases | fresh_racing | -0.00792934 | [-0.0132634, -0.00320843] | 5 / 0 / 0 |
| all_cases | reuse_racing | 0.000215842 | [0, 0.000647527] | 0 / 4 / 1 |
| all_cases | global_racing | -0.00783538 | [-0.0203564, 0.000440805] | 2 / 1 / 2 |
| all_cases | driftqas_racing_uniform | -0.00489635 | [-0.0125837, 0.00279101] | 3 / 0 / 2 |
| stable | reuse | -0.00367065 | [-0.0197716, 0.0124303] | 3 / 0 / 2 |
| stable | driftqas | -0.00367065 | [-0.0197716, 0.0124303] | 3 / 0 / 2 |
| stable | ideal_only | 0.00101942 | [-0.0200962, 0.0205018] | 2 / 0 / 3 |
| stable | fresh_racing | -0.0103975 | [-0.022949, 0.000753873] | 4 / 0 / 1 |
| stable | reuse_racing | 0 | [0, 0] | 0 / 5 / 0 |
| stable | global_racing | 0 | [0, 0] | 0 / 5 / 0 |
| stable | driftqas_racing_uniform | -0.00265914 | [-0.0102963, 0.00655866] | 3 / 1 / 1 |
| abrupt-stress | reuse | -0.0171869 | [-0.0377539, -0.00315482] | 4 / 1 / 0 |
| abrupt-stress | driftqas | -0.0046659 | [-0.010867, 0.0015352] | 3 / 1 / 1 |
| abrupt-stress | ideal_only | -0.0885669 | [-0.204181, -0.00601376] | 5 / 0 / 0 |
| abrupt-stress | fresh_racing | -0.00546123 | [-0.0119484, -0.00140588] | 4 / 1 / 0 |
| abrupt-stress | reuse_racing | 0.000431685 | [0, 0.00129505] | 0 / 4 / 1 |
| abrupt-stress | global_racing | -0.0156708 | [-0.0407129, 0.000881611] | 2 / 1 / 2 |
| abrupt-stress | driftqas_racing_uniform | -0.00713355 | [-0.0148711, 0.000603951] | 3 / 1 / 1 |

## Coverage and resource diagnostics (all cases)

| Policy | Mean regret | Budget used | Confirmation coverage | Model coverage | Zero confirmation SE |
|---|---:|---:|---:|---:|---:|
| reuse | 0.021594 | 98.4% | 95.0% | 80.0% | 0.0% |
| driftqas | 0.0153335 | 98.4% | 95.0% | 82.5% | 0.0% |
| ideal_only | 0.054939 | 19.9% | 100.0% | 90.0% | 0.0% |
| fresh_racing | 0.0190946 | 99.9% | 97.5% | 77.5% | 0.0% |
| reuse_racing | 0.0109494 | 100.0% | 97.5% | 82.5% | 0.0% |
| global_racing | 0.0190006 | 100.0% | 97.5% | 82.5% | 0.0% |
| driftqas_racing | 0.0111652 | 99.9% | 97.5% | 85.0% | 0.0% |
| driftqas_racing_uniform | 0.0160616 | 99.9% | 95.0% | 80.0% | 0.0% |

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

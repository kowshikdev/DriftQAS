# Implemented methodology

## Experimental scope

This milestone is a chronological, fixed-library comparison. Every policy receives the same
candidate bank, ideal-trained parameter vectors, task, initial measurement schedule,
calibration stream, and per-epoch shot limit. Bank preparation is shared and reported as
ideal objective calls and wall time. It is not free full-search training.

The task does not change during an episode. Calibration snapshots contain synthetic local
CX depolarizing probabilities. Single-qubit and basis-change gates and readout are ideal in
this initial model. Logical RY/RZ/CX circuits compile onto a fixed bidirectional chain with
an explicitly recorded mapping and compiler seed. A hardware-native adapter is not implemented.

Candidate specifications have zero to three entangling layers, each with RY or RY/RZ
rotations and optional directed nearest-neighbor entanglers, followed by a rotation block.
H₂ starts from X on qubit 0. At most 48 rotation parameters are needed for six qubits.
Specifications are unique; different redundant parameterizations may compile to equivalent
architectures. The prototype does not certify a nonredundant or exhaustive search space.

## Evidence model

An observation is identified by task, architecture, parameters, compiled conditions, source,
shots, and measurement seed. Raw group counts are retained. Historical calibration is stored
with the result, never replaced by the latest snapshot.

The ideal energy is a shared prior. A fixed-kernel Gaussian process models measured noisy
energy minus ideal energy, using architecture/depth/parameter features, compiled edge counts,
and count-by-current-error exposure features. Every informed policy uses the same model family
and available context features.

For DriftQAS, historical exposure is:

`D = sum(native_CX_count_on_edge * abs(new_error - old_error) / drift_scale)`.

Relevance is `exp(-forgetting * D)`, clipped at an exponent of -20. Discounting increases
observation transfer variance; it does not rewrite the historical measurement as a current
unbiased label. Global forgetting instead uses a circuit-independent maximum edge-error
change. Unchanged reuse applies no extra transfer penalty. Ideal observations are retained
as evidence for the ideal objective, not forgotten because hardware changes.

Kernel amplitude, feature scaling, discounting, and uncertainty-based selection are prototype
heuristics. Their uncertainty is not certified calibrated. Development tuning and held-out
coverage/ranking checks are required before a research performance claim.

## Allocation policies

- Random allocates uniformly among eligible candidates, then uses the shared model for its
  final recommendation.
- Restart discards old noisy observations at the start of an epoch and pays for fresh seeds.
- Reuse keeps observations without additional drift discounting.
- Global forgetting applies one hardware-change discount regardless of circuit dependence.
- Periodic refresh rechecks up to three previously observed leading candidates every epoch.
- DriftQAS refreshes leading candidates whose compiled footprint is exposed to observed drift.

Outside refresh actions, informed policies select by predicted mean minus 0.5 model SD.
An unseen current candidate receives the low-shot allocation; a promising measured candidate
is promoted toward the high-shot allocation. Current-epoch repetition is capped at roughly
twice the high-shot allocation per candidate. Affordability can truncate an allocation.
This staged policy is not an optimal joint knowledge-gradient implementation.

## Measurement uncertainty and budgets

Hamiltonian terms are greedily grouped when they commute qubit-wise. Each bitstring supplies
the sum of that group's weighted Pauli outcomes. Computing the sample variance of this sum
retains covariance between terms. Independent group mean variances are added. Identity terms
contribute exact constants and require no shots.

Total shots equal the sum over every executed group's requested allocation. Charge before
execution; an execution failure conservatively retains the reservation and is logged. This
initial implementation aborts instead of silently retrying or assuming failed work was free.

Confirmation is reserved and the recommendation is locked before those fresh measurements.
Its stream is distinct from search streams. The result can be used in subsequent epochs
only. SHA256-derived per-candidate/epoch/phase/repetition streams make replay deterministic
and share random numbers across matched policy actions.

## Independent scoring

After all policy episodes finish, a separate density-matrix evaluation computes current noisy
prepared-state energies for the frozen bank. Offline selection regret is the recommended
candidate's energy minus the best bank energy at that epoch. Ground-state excess uses the
exact eigenvalue of the same Hamiltonian. Audits are logged as not policy-visible.

Confirmation measurements remain separate from these analytic audit scores. Neither an
optimistic sampled energy nor an audit reference is used to retroactively replace the locked
recommendation. A single development seed is not a statistical research comparison.

## Remaining milestones

The complete plan also calls for held-out repeated-seed studies, broader drift/mismatch
controls, ablations, calibrated predictive uncertainty, a source-aware acquisition algorithm,
architecture mutations, and noisy parameter-training costs inside the online budget.
Automatic interruption recovery and a QPU/calibration adapter remain unimplemented.

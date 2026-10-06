# Preserved first calibration attempt

The first primary calibration attempt used frozen ID
`abf04b22582031bdb6619e5d1ec63a603752f0847b630428f8719845fad02970` and suite digest
`b7a62e7be9334e1ea762f897f246b75c16f6c73ebb0da15c8b493f53820a7089`.
All 80 declared computational episodes finished. Final complete-pair verification then
failed because five environment-created temporary entries had been inadvertently captured
by recursively sealing every file in an attempt directory. A temporary entry later changed.
The suite remained **failed**; it was not exported as a successful result or used for fitting.

Read-only checks found zero mismatches in the original hashes for canonical experiment
artifacts. All 80 episodes also passed outcome/ledger validation and full database/JSONL
event parity. The defect was the inclusion of non-experiment transport files, not missing
measurement data. The failed raw attempt and its original receipts were preserved unchanged.

The fix seals an explicit artifact set: five core files plus every declared policy/epoch
QASM. New tests check that changing a temporary file does not affect a seal, changing a real
artifact still fails checksum verification, and missing QASM prevents sealing.

A new source/environment freeze was created and calibration was rerun from scratch, with
the **same cases, policies, hyperparameters and calibration seeds**, before any primary
held-out execution. The old freeze is retained alongside v2. This extra run consumes
resources but is not an additional independent calibration sample or a favorable-seed
selection. No held-out results were available when the fix or new freeze was chosen.

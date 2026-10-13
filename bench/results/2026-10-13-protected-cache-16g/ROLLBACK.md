# Activation, deployment and rollback limits

The v1 GPU acceptance gate failed on zero compaction gain and exposed short-turn overhead. The candidate was not deployed; the baseline API was restored and independently verified healthy. This preservation bundle does not deploy anything. The original source is a historical executable lineage, not current-main source. Do not copy the changed checkpoint-layout header into a binary built with stale structure-owning objects.

## V2 deployment hold

V2 binary `2cbcd0eafb1385e4a345bb405e8c677e9fb77f3cbba46088d04c760fdd246ef2` passed its 20-request test contract but is **not deployed**. Ancestor-return prompt time regressed 962.7→82993.6ms, so deployment remains blocked pending diagnosis and revalidation. The old baseline remains the rollback/production reference; no `passed=true` test receipt overrides this hold.

## Activation requirements

Before activation, verify both CPU receipts, the candidate binary SHA256, paired GPU output/input parity, compaction reduction, decode-anchor restoration, cancellation recovery, per-request optional-cache accounting, and cleanup/recovery of the test window. Check the actual API and model health independently: requesting a container start is not health verification.

Change only the explicitly reviewed executable and add `--prompt-cache-protected` after validation. Preserve PP 4096, spec 6, split 27, maximum context 262144, parked cap 12288 MiB, four parked slots and the 8192 MiB minimum-free floor. Do not enable batch, pipeline or disk persistence as part of this deployment. A successful text replay does not authorize claiming image or tool-quality validation.

## Rollback artifact

The CPU builder retained a byte-identical baseline binary with SHA256:

    74aa76d48a4783991e60b7e25601125dc5dc2bfeeaa351a71b350c122476b662

Candidate binary:

    7b00d34c85181a2023862e01a5782c68c0403ba5b13a0e0eeec7280afa06b0e6

Rollback requires the known baseline executable and its prior launcher/configuration, with the protected flag removed. Stopping/restarting the service loses in-memory cache state. Reusing the new header with old objects, downgrading a running in-memory layout, or assuming disk compatibility is safe are not supported rollback methods.

Preserve verified rollback files before changing a live executable or launcher. If GPU replay fails parity, memory accounting, state restoration, cleanup or recovery, keep the baseline deployment and report the failed gate. An SSH connection drop alone is not evidence that a detached server-side test failed; reconnect and check its terminal receipt without launching a duplicate job.

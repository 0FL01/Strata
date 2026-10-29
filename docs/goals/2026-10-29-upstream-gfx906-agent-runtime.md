# Upstream gfx906 and agent-runtime goal   -  2026-10-29

Improve applicable agent-runtime correctness and measured PP/TG without a wholesale
upstream merge. Work iteratively: reproduce the baseline failure, make the smallest
change, run isolated tests, obtain review, and retain negative results.

## Published scope: Chat tool-result association

Based on upstream11237f831f3cc4691369186d3c51e90ac4b59a6d. Preserve call IDs until
normalizing Chat history. Reorder a contiguous result run only when the preceding
assistant call IDs and result IDs are complete, unique, nonempty strings with
identical sets. Ambiguous, missing, duplicate and partial IDs keep received order.
Private IDs are removed before rendering. Tool arguments and input objects are
not mutated. Existing ordered and legacy prompts remain identical.

Only serve/frontend.py changes executable production behavior. No server/native
code, model settings, GPU kernels, defaults for performance experiments or service
deployment is included. This is a correctness fix, not a speed claim.

Validation:10 focused tests and27 existing frontend regressions pass on the
main-based tree. They cover permutations, multiple turns, malformed IDs, mixed
image/text result association, input immutability and in-process Service.prepare.
Tests run with no network, Docker socket, GPU devices or writable source; a Python
audit hook rejects process launches, socket operations and process signals.
Run tools/run_agent_toolorder_cpu.py inside that isolated environment mounted at
/src. CPU mocks are not native/model or deployment qualification.

## Retained research, not installed by this publication

The deployed legacy Python was separately snapshotted, preserving local changes.
Its nonfinite/cancellation overlays are NOT substitutes for newer main server.py.
Local checkpoints remain remote:00d5fdd4(nonfinite),dcc61843(quiet cancellation),
6bcf3f3d(FIFO ownership),1307a96a(preparation cancellation),e5b88821(cross-protocol
tool ordering). These are independently scoped offline candidates, not a tested
composition on this publication tree.

PR4132 headaffadaa4a2375363d7159cfbf48168ae14a8ef7f is rejected for now: its own tests
pass but21 adversarial direct/stream cases fail. A depth experiment fixes14, not
the7 unfinished-opener cases. No parser experiment is installed.

## Pending hypotheses and gates

- Reconcile live serial nonfinite handling fromf332a855, preserving local prefix
  diagnostics and reasoning-close behavior. Main already has newer handling.
- Cancellation423f5893/875d6a92/873a0d66: preserve ownership, bounded polling and
  between-image checks; do not imply interruption of a synchronous encode.
- Native copy pool3478382: actual-header CPU model shows bounded handle reuse;
  hardware/error-path qualification remains pending. Companionf62589 has a
  wrong-device error-check counterexample and must not be imported blindly.
- PP routed issuer PR4283(ab73738f4cf19503ff746d76e40acd07b0c42531): review
  concurrent logging, event-error propagation and selected-route applicability.
- Sparse eventsa11f8b0a requiref217b23 and an additional captured-state lifetime
  fix. Do not stack with the alternate PP issuer without integrated proof.

Any future native/GPU or temporary service test needs a frozen reviewed plan,
live-work check and exact original-model restoration. No main publication implies
deployment. No speed claim without matched workload measurements.

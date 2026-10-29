# Goal: upstream gfx906 performance and agent API correctness

## Method

For each hypothesis: reproduce the baseline defect, make the smallest compatible change, run isolated tests, review the complete composition, and only then decide whether to publish. Performance needs matched measurements; CPU correctness tests are not performance or live deployment evidence.

## Checked API changes

The historical first phase (main 9103b410) fixed Chat tool-result association. This phase extends the same complete, unique ID matching to Anthropic and Responses, and fixes cancellation at FIFO ownership and request preparation boundaries. Executable changes are limited to serve/frontend.py, serve/responses.py and serve/server.py.

- Exact-main protocol tests reproduced reversed Anthropic results and malformed/ambiguous Responses ID handling.
- Exact-main server tests reproduced cancellation before or during successful FIFO acquisition, and preparation continuing after cancellation.
- Final combined suite: 97 tests passed, including converter permutations, malformed/partial IDs, multimodal results, repeated turns, FIFO ownership, image preparation cancellation, and fake-engine handler tests for all three API protocols.
- The suite also passed from a different checkout path. Tests derive fixture paths from their source file.
- Existing main nonfinite accounting and quiet polling passed 15 tests unchanged; legacy server overlays were not copied into main.

Run the selected CPU suite with tools/run_api_adaptation_cpu.py in an isolated CPU container without network, Docker socket, GPU devices or production configuration. The runner denies socket and external process effects. No live deployment or restart is part of this publication.

## Limits and remaining hypotheses

Partial or ambiguous tool IDs preserve arrival order; they are not claimed semantically repaired. Cancellation is checked between synchronous download/encode calls, not inside those calls. Batch/replica ownership paths are unchanged. Fake-engine tests do not establish real GPU, disconnect-latency or vision-model performance.

Quoted-tool-call PR #4132 is not included: adversarial parser fixtures exposed unresolved ambiguity. Vision-cache file lifetime across concurrent preparation was subsequently reproduced and corrected as described below. Native checkpoint-copy and prefill performance experiments remain pending; no native code or performance default is changed here.

## Concurrent image preparation

A deterministic two-thread CPU test reproduced a cache lifetime bug: one request released the image turn before copying its cached embeddings, allowing another request to evict the first request's source file. The fix retains that acquired turn until preparation returns or raises. Text-only requests acquire no image turn; image cache limits, context validation and caller cleanup remain unchanged.

The same interleaving now passes, including a copy-error unwind followed by a waiting request. Eight ownership/cache tests plus the existing API suite pass: 105 total. These use actual preparation/cache code with fake encoder I/O, not a vision model or GPU. Holding the turn through copying may increase queue time; no speed improvement is claimed. Cancellation does not interrupt a synchronous copy already in progress.

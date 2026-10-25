# Cooperative reasoning-budget segments (experimental, default OFF)

This frontend-only experiment preserves the configured reasoning and total-output budgets. It caps the native request at the next reasoning-budget boundary, rather than interrupting a larger native request after that boundary. A natural length completion preserves the usable live prefix before the existing closing text is appended.

Enable only with `STRATA_REASONING_NATIVE_CAP=1`. Eligibility is conservative: greedy text, non-batch, pipeline-windows=2, mtp-max-t=2, suffix-draft=0, no-coupled-draft, and neutral repetition/presence/frequency penalties. Unsupported profiles retain the legacy path. This does not enable a production API or alter the default configuration.

## Why this matters

In the measured task the frontend delivered 3072 reasoning tokens, while asynchronous STOP drained two additional native tokens. The existing closing text is **18 tokens** with the qualified tokenizer, not 16. The cache mismatch forced a continuation to reread 3095 tokens. Natural completion at the cooperative boundary instead reused the live prefix and read 19 tokens. No recurrent-state rollback, cache truncation, or native kernel change is used.

Internal segment limits are not user-visible output limits. Early reasoning closure can continue transparently with the original remaining output budget. Parser/UTF-8 boundaries, natural stop/EOS, cancellation, errors, and existing close-retry eligibility remain explicit. Fresh native DONE accounting is required; no-progress and malformed completion fail closed.

## Frozen reasoning-ON 8K task screen

Two MI50 GPUs; published HC BF16 baseline with wide dequantization enabled for this local research comparator. One deterministic dependency-order repair task, actual bounded local tools, and an external value oracle. A is legacy, B cooperative. The pilot, interrupted earlier block, and separate reasoning-OFF trials are excluded.

| Fresh arm | Task wall (s) | Output tokens | Hidden cases |
|---|---:|---:|---:|
| A | 128.465234 | 6081 | 14/14 |
| B | 103.231548 | 5129 | 14/14 |
| B | 103.478128 | 5129 | 14/14 |
| A | 128.558937 | 6081 | 14/14 |

Mean task wall: **128.512085 -> 103.354838 s**, a **19.5758% reduction**. Both paired reductions are positive (19.6424%, 19.5092%). This passes the prospectively frozen engineering screen (at least 3% pooled reduction, positive pairs, correct repair and completed tool work). It is not a statistical confidence claim.

All four runs produce the identical repaired file and completed tool work. The first four delivered turns match in reasoning, content, arguments, and counts. Their patch turn averages **68.717707 -> 60.260323 s** (12.3074%, 8.457384 s). Continuation PP is **9138/9104 -> 132/132 ms**, reading **3095 -> 19 tokens**.

Later reasoning and final explanation differ; total outputs fall from 6081 to 5129. Therefore the full 25.157248-second task reduction is **not** an equal-token native-throughput improvement. Native draft work also differs. Both versions retain a known explanation error about duplicate task emission; no new material false test-execution or completion claim was found. Correct code and hidden tests do not establish that every prose statement is correct.

A separate original resolver task with the feature ON matched its retained nontrigger trajectory and tool work exactly (1213 outputs, six turns, eight calls; 5/5 hidden cases). Its wall time was not an admission gate. No 64K cooperative-cap qualification or broad agent-quality claim is made.

## Source and evidence identity

- Parent published commit: `f9b38e9e5d70cef7776f2a5bd6fed5e56872ec02`.
- Unchanged native executable SHA256: `04761771491379c012b29bbc969628339cc0c98bf0cd7471277acf5bf6872176`.
- Measured frontend SHA256: `9225e3448107f1604cfe4e6624ed558a70f6504d837f0f6a6fd487a6412b46a0`.
- Hardened frontend SHA256: `962503be30a8c465754bdcaa4d5498526005b1ac0c7850007e0d017dfd91682c`.
- Frozen protocol SHA256: `7066a94fcc897244785d590499a94dfc002f262b41d7eda0ce44b0829f8c7ace`.
- Private retained 90-file evidence manifest SHA256: `b9f8b66eeb706f3256d255a9a55b4af4e81de1e30c940096d829282351af9432`.

The hardened source adds only a six-line admission restriction after the measured version: non-neutral or malformed penalties fall back, since penalty history can make native generation choose serial decoding despite pipeline arguments. The measured plans have no penalties, so their admitted execution path is unchanged. Hardened frontend CPU results are recorded separately; no new GPU measurement is attributed to this hash.

## CPU regression

`serve.test_reasoning_native_cap` uses the actual Service and tokenizer with a simulated native generator; it starts no native model process. Set `STRATA_TEST_TOKENIZER` to a compatible qualified tokenizer directory containing vocab.json, merges.txt, and token_type.json. The fixture requires the 18-token closing text; without this setting the tokenizer-dependent class explicitly skips.

Run from the repository with the tools directory on PYTHONPATH:

```sh
PYTHONPATH=.:tools python -m unittest serve.test_reasoning_native_cap serve.test_request_accounting serve.test_server -v
```

Hardened source: **360 CPU tests passed in 117.946 seconds**, including the 347 existing server/accounting tests and 13 cap tests, with the tokenizer configured (no skips). No GPU rerun was needed for the admission-only restriction.

Coverage includes exact supplied prefixes, early closure, UTF-8/tag boundaries, natural stop at a cap, cancellation/error, missing or inconsistent DONE, global-budget exhaustion, legacy OFF parity, unsupported profiles, and penalty admission. Tests do not prove all real-model prompts have identical trajectories.

This branch records an experimental opt-in frontend and research result. Main, production settings, native code, and rollback configurations are unchanged.

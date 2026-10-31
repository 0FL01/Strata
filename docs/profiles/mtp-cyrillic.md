# MTP Cyrillic draft shortlist

This opt-in configuration fragment uses the existing draft-only vocabulary override.
It changes no native code or global defaults. The full target verifier, target vocabulary,
model quantization and MTP weights are unchanged.

## Apply to an existing server configuration

[mtp-cyrillic.json](mtp-cyrillic.json) is an **argument fragment, not a complete server config**.
Append its two arguments to the existing `args` array. If `--mtp-draft-vocab` already
exists, replace its value; do not add duplicates. Preserve all other keys and arguments.
The example path assumes the repository is mounted at `/src`. Otherwise change only
the path to an absolute path visible to the native process.

Before restarting, preserve the exact old configuration and verify the file:
- Repository file: `data/draft_vocab_cyrillic.bin`.
- 58,963 distinct little-endian int32 token IDs; 235,852 bytes.
- SHA256: `25d7fd1670a2e0ec885868d1718d410a3baab03bceeacf0a156cf93ffe4e1ef4`.

The server forwards `cfg["args"]` to the engine. Keep existing target, expert-cache,
layer-split, context, KV, pipeline and sampling settings. Do not import experimental
exactness flags or fixed expert-slot counts from a benchmark. A smaller draft head may
change automatic expert-cache admission; verify the actual startup counts.

Run `python3 tools/test_mtp_cyrillic_profile.py` for the fragment/data/argument-forwarding
CPU checks, including effective-environment override precedence. These do not replace
GPU or live API validation. A faithful benchmark must use the server's effective
child_env(cfg), not just the container environment: cfg.env overrides inherited
values. Omitting it can silently benchmark a different approximation profile.

## Evidence, not a universal speed promise

On two MI50 gfx906 cards with the previously qualified native build:
- Cold 64K input / 4K output: +2.11% and +1.81% TG in opposite-order pairs.
- One Russian task (163 input / 1024 output): +38.9% and +46.6% TG,
  approximately 25–26% lower total request time, but worse TTFT.
- One code task (116 input / 1024 output): +1.33% TG in one pair, not a stable-gain claim.
- Every compared output token was identical. Fixed-cache READY memory fell about
  79.4 MiB on the second GPU. No PP acceleration is attributed to this setting.

Those measurements used greedy, fixed-length generation with EOS disabled and explicit
exactness controls. They are not proof for every production profile, language or task.
Smaller draft vocabulary can improve or worsen acceptance. Validate representative
requests under the actual deployment settings before adopting it.

The [pinned research report](https://github.com/0FL01/Strata/blob/05e996d7ec2e11107eff65eb2d22997e7e911950/docs/goals/2026-10-31-qengine-gfx906-results.md)
contains the full measurements, negative experiments and limitations. The mechanism was
already in Strata; no QEngine implementation or asset was copied.

## Deployment-profile qualification (2026-10-31)

A fresh bounded native comparison retained the deployed model, native binary, cache
arguments and the complete effective server environment, changing only the draft
vocabulary. Greedy generation used 1024 output tokens with EOS disabled. Russian ran
default then shortlist; code ran shortlist then default.

| Task | PP default → shortlist (tok/s) | TG default → shortlist (tok/s) | Request time (s) | TTFT (s) |
|---|---:|---:|---:|---:|
| Russian, 163 input | 79.13 → 78.84 | 42.96 → 63.63 | 25.91 → 18.17 | 2.294 → 2.301 |
| Code, 116 input | 58.57 → 63.29 | 76.21 → 78.09 | 15.43 → 14.96 | 2.214 → 2.068 |

All 1024 output IDs matched within each pair. Output SHA256:
- Russian: 2c75237ce0e5334713cfe3b42dc574c2f75f636266e833dcdda40db027b5bb55.
- Code: dcd306a89844319f22a4612553da2454e5ba8391c559957c7255ae4f34bbe486.

Automatic cache admission yielded 18,018 expert slots in all four runs; it was not
forced to that number. Draft head allocation was 178.4 → 99.0 MiB. This is one
qualification pair per task, not a broad performance distribution or a PP speed claim.
The deployed profile already set tail skipping to 0 and IQ_MT_MIN to 1; qualification
did not introduce those changes.

An initial attempt omitted the server configuration environment overlay and therefore
tested a different approximation profile. Its token mismatch is **not** evidence about
the actual production profile, and its timings are excluded above. The corrected run
used the actual live child_env function, including all configuration overrides.
The earlier research measurements remain controlled research results, not a claim that
every effective production environment variable was reproduced.

## Verify and roll back

After restart, verify the loaded draft vocabulary has 58,963 rows, the full verifier is
unchanged, and health, normal generation, tool history, streaming cancellation and error
recovery work. Compare actual arguments with the saved baseline, allowing only this
vocabulary override. Preserve the original model and MTP pack.

To roll back, restore the exact prior configuration and restart. If there was no previous
override, removing the two arguments restores the MTP pack's default vocabulary. Do not
overwrite the pack's original `draft_vocab.bin`.

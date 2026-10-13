# Bounded paired replay launcher

`replay.py` drives the native protocol and compares the two arms. `run_gpu_replay.py` is an explicitly admitted operator launcher for sequential runs, GPU exclusion, temperature sampling, owned-container cleanup and recovery of a previously running API container. It does not install the candidate or change configuration/model/source files.

The public launcher's host mount paths are sanitized `/srv/...` examples. Confirm the real paths, model mounts, GPU PCI IDs, group IDs, existing lock, container identity and production configuration before use. Do not execute it against a different host simply because the examples exist. The unchanged original-source hash and public-copy hash are recorded in `source-pins.json`.

The original `prompt-65536.ids.json` is intentionally omitted. A measured replay requires the authorized operator's exact seed with the SHA256 in `source-pins.json`. Never substitute the public CPU test's synthetic seed while claiming reproduction of a measured GPU result.

For a verified host, supply all explicit inputs:

    python3 -B run_gpu_replay.py --gpu-window-approved \
      --production-config VERIFIED_PRODUCTION_CONFIG \
      --baseline-binary VERIFIED_BASELINE_BINARY \
      --baseline-sha256 74aa76d48a4783991e60b7e25601125dc5dc2bfeeaa351a71b350c122476b662 \
      --candidate-binary VERIFIED_CANDIDATE_BINARY \
      --candidate-sha256 7b00d34c85181a2023862e01a5782c68c0403ba5b13a0e0eeec7280afa06b0e6 \
      --build-receipt VERIFIED_ORIGINAL_CANDIDATE_BUILD_RECEIPT \
      --out FRESH_RESULT_DIRECTORY

The pinned production environment is preserved in `production-environment.json`. The launch uses no network and read-only source/model mounts; candidate and baseline flags differ only by the protected flag after shared replay-only EOS settings. `--prompt-cache-spread` is enabled for both arms to match the baseline launcher even if the configuration JSON omits it. Protected retention takes precedence in the candidate.

This13-request v1 replay completed with overall acceptance=false: both arms resumed 100786 for compaction and read 16604 tokens, giving no gain. Inputs and comparable output IDs matched, and decode-anchor/cancellation/accounting checks passed. The original root collapse was not reproduced. Six ordinary short turns took 5.26% longer in wall time. A separate exact-history stress fixture and overhead investigation are required; this v1 candidate was not deployed. See [the result](../evidence/replay-v1/summary.json).

Normal acceptance requires `protocol_passed=true`, `protected_gates_passed=true`, paired input/output parity, reduced compaction work, decode-anchor reuse, bounded accounting, unchanged inputs, owned-container cleanup and successful recovery if the API was initially running. A start request is not an API/model health check. See the parent [VALIDATION.md](../VALIDATION.md) for scope and timing interpretation.

The wrapper bounds loading/requests/arms, samples temperatures, refuses to kill foreign jobs and cleans only exact-name/exact-owner containers. It leaves an initially stopped API stopped. Host loss or an unavoidable SIGKILL still requires operator recovery. After an SSH network drop, check the independently running job rather than assuming failure or duplicating it.

Capture diagnostics need careful interpretation: event `bytes` is the entire checkpoint bank, and `ms` measures checkpoint_at/assembly without all earlier multipart on_stage_chunk save time. Use end-to-end prompt, first-token and wall timings for real overhead; neither field can be summed into total snapshot traffic/cost.

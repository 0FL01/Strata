# Second gfx906 Hybrid campaign

Baseline: deployed 82f4473, runtime cc7eeb6, seven previously qualified settings.
Two gfx906 16 GiB cards, Xeon E5-2698B v3, 128 GB RAM.
Model and 204800 capacity unchanged. Work began 2026-10-07 08:20 UTC.

## Upstream overlap review

168 open PRs inspected at 08:22 UTC. Existing Q2 work is #1187; exact-path tests are now #1320.
- #1316: stale lookup-cost re-probe; candidate for independent adoption test, do not duplicate implementation.
- #1296: WY recurrence already loses on author's gfx1100; no matrix cores here. Low priority.
- #1237: pinned staging applies when the full resident arena is unavailable; ours fits. No expected steady-state benefit.
- #1282: CPU prefill share currently single GPU. Not a drop-in layer-split optimization.
- #1247: exposes existing prefill-helper settings as CLI; no new compute implementation.

## Screened paths

- Idle-stage prefill helper: current gfx906 binary has MMQ disabled. set_stage_helper exits when mmq_plan().any is false. Enabling STRATA_PREFILL_HELP alone cannot activate it. Prepared helper benchmark was not launched; avoid benchmarking a proven no-op. Supporting this route would require a separate backend implementation.
- Prior campaign's pipeline output divergence, shared-stream loss and planner noise remain documented in ../2026-10-07-gfx906-campaign; no blind repeats.

## Pending

Profile current paths, test transposed reductions with independent parity checks, test Q2 gate/up bit spreading, and evaluate #1316 separately. No new speed claim yet.

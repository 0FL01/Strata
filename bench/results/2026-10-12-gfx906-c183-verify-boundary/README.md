# HC N4 verify-boundary observer

**The earlier ON slowdown did not recur in this diagnostic pair; the four prior negative TG pairs remain unresolved.** This changed-host observation neither fixes them nor establishes zero loss.

One 64K/1,024-output OFF→ON pair used a new host-only observer after reproducing both baseline host objects. Existing GPU code was reused. Six added host clock reads/window plus rare capture reads add overhead; no GPU events, synchronization calls or warmups were added. This is not performance qualification.

- Decode: **19,494.2→19,000.8 ms (−493.4 ms)**. PP+decode: **120,860.0→118,321.2 ms (−2,538.8 ms)**.
- Outer verify: **17,599.038518→17,097.022369 ms**. Primary polling wait changes **−285.049571 ms**; inclusive peer changes **−53.849778 ms**. These nested host spans are not additive GPU timings.
- All capture spans: **331.437096→172.939600 ms**. Verify-minus-captures changes **−343.518653 ms**; subtraction does not create a warm benchmark.
- Primary cold T2 instantiate/destroy: **196.170272→8.029045 ms**. The other 47 T2 windows total **1,562.509589→1,562.019089 ms**.
- OFF's later T4 maximum is **338.061519 ms**, versus first **70.907296 ms**. It is not the cold T4 capture; aggregates cannot tie this outlier to an owner's wait or identify a cause.

Both arms retain historical output/work equality and 379 windows. Independent actual audit: **532 checks**; cleanup **52 C**, API stopped.

`instantiate_ms` includes graph instantiation **and destruction**. Commit capture includes recording, instantiation and destruction, with no separate upload/sync phase. See [metrics](metrics.json) and the [retained unfavorable results](../2026-10-12-gfx906-c183-hc-bf16-n4-baab-length/README.md).

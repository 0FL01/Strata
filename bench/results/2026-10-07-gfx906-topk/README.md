# gfx906 large-capacity decode top-k experiment

Pinned baseline82f4473, separate opt-in STRATA_GFX906_TOPK_REG=1.
Only uncounted gfx906 decode calls with at most8 queries may use the existing
66-key register kernel through its conservative capacity bound. Default,
counted/prefill policy, old-kernel override and other architectures are unchanged.
No scorer arithmetic or selection order changes.

At main capacity204800 the old uncounted dispatch selects the256-thread
reference kernel because51202 capacity blocks exceed the33-key bound33792.
The66-key bound67584 covers this capacity. Device steps still determine actual
active cells on every captured replay; no active count is frozen on the host.
Opt-in STRATA_TOPK_TRACE records the selected route once per device/route.

## Component evidence

Two gfx906 cards,48 cases: actual contexts4096/8192/16384/32768/65536/131072/
200000/204800, query counts1/4/6, capacity204800. Every consumed selected ID
matches the original reference for continuous, tied, equal and adversarial
NaN/signed-zero/poisoned-inactive-suffix scores. Output end canaries pass.
The same graph is replayed across short and long contexts with changed steps.

Representative4-query timings:
- 64K: reference0.290ms versus register0.192ms (~1.5x).
- 131K:0.52ms versus0.335ms.
- 200K:0.554ms versus0.44ms.
- Short4K regresses:1 query0.089ms versus0.110ms.
This is not a whole-model TG claim. Model screening is pending.
The existing32KiB LDS/1024-thread kernel is unchanged; no general gfx906
register/occupancy claim is inferred from the RDNA source comment.

## Follow-up

If whole-model short-context regression matters, test complementary device-side
guards on the two existing kernels, measuring the extra no-op launch. Do not add
new graph buckets or capture a host-side active count.
Keep this opt-in until model evidence supports promotion.
See components.json for every case and executable hash.

Upstream overlap reviewed: PR337 introduced the counted HIP66-key route and
left decode unchanged; PR603 streaming kernel is excluded from HIP; PR575
is a prompt split/merge alternative. Current PR1151/1298 concern approximate
prompt scorers. This experiment does not copy those approximate paths.

# c183 PP shared fork: small descriptive signal, parked

**Park the fork; no PR or promotion.** This report retains the observer, failed V1 admission and corrected V2 experiment.

The serial observer measured shared-operation event envelopes of **2.634 s on GPU0 / 2.060 s on GPU1**. These include submission gaps and must not be summed as wall savings; they establish no overlap benefit.

**V1 failed before admission.** A matrix-only dimension guard rejected 48 valid one-dimensional scalar gate vectors. OFF used 768 serial fallbacks, with zero fork launches/joins; ON never started. This is neither a memory-pressure finding nor fork performance evidence.

After the guard correction, one fixed-order **OFF→ON** pair processed 65,536 prompt tokens and one output per arm:

- Prompt time: **101,301.5→100,544.3 ms**, saving **757.2 ms**
- PP: **646.940→651.812 tokens/s (+0.753101%)**, descriptive only
- All 16 progress intervals improved by **7–112 ms** (median 39); 757 ms plus 0.2 ms tail reconciles the total
- ON recorded **432/336 joins**; both arms allocated **38 MiB extra per owner**

V2 compares the original serial handle with a second-handle fork. Order and handle-state effects remain confounded. Only the first historical output and available work/INFO match; full trajectories, TG throughput and peak VRAM are unqualified. Integer progress intervals are not isolated GPU timings, and none were excluded.

Independent audits cover observer **152 checks**, retained V1 failure **172**, and V2 **223**, plus the chunk supplement. Cleanup passed, API stayed stopped, final sampled maximum **54 C**. [Aggregate metrics and provenance hashes](metrics.json).

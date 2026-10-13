# Q2 grouped-expert component correctness

**PASS: 144 cases / 864 grouped calls across both MI50 GPUs.** One fresh Q1 process per owner, in ordinal 0 then 1 order, passed 72 cases and 432 calls each. Physical binding was verified, both exits were zero, stderr was empty, and all ordered verdicts were retained. Independent actual review passed 255 checks; cleanup/API-off passed, final maximum 45°C.

Each case compares six calls within the same candidate executable: gate/up mode 7→13, down-only 13→15, and complete 7→15. Checks cover FP32 bytes, complete q8 blocks/metadata, consumed outputs, finite writes, inactive zeros, input immutability, padding/guards and down-only scratch. Alternate poison checks write coverage, not NaN-input arithmetic.

Per owner: six shapes × four group plans × grids 0/1/7. Shapes include both Q2 paths, gate/up-only, down-only with existing LDS gate/up, neither path, and H=2304/FF=576 refusals. Plans include empty-offset, singleton, full and scattered groups. Empty plans still write h/q8. The 24 input quantizations are source-derived/harness-printed, not independently runtime-counted.

**Model results and performance remain pending.** The component receipt retains baseline-preservation=false and model-admission=false. A later, separate bounded mode7 static bridge covers six reviewed shapes under stated conditions; a fresh metadata census binds 48 expert layers / 144 tensors to H=2560, FF=640, gate/up/down type 42. Neither establishes runtime dispatch or equivalence for the **other 151 changed baseline device bodies**.

No separate B0 numerical comparison, device-route trace or performance timing occurred in this suite. This finite matrix does not establish model-wide/all-format correctness or a speedup. [Metrics and evidence hashes](metrics.json) preserve the distinct receipt scopes.

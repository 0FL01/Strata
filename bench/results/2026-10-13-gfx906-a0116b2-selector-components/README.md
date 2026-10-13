# REG2 / FIT17 selector build and component evidence

**B0, S1 (REG2), and S2 (REG2+FIT17) pass the bounded component suite on both owners, using distinct harness epochs.** This supports the existing [REG2 PR #1535](https://github.com/Niko1221/Strata/pull/1535) and [FIT17 PR #1743](https://github.com/Niko1221/Strata/pull/1743); model and performance qualification remain pending.

Fresh builds are based on `a0116b2782a5b82622358c04a06496485d12b2d6`. Later independent linked-image/ISA review resolves the original build receipts' pending instruction-review gate.

- **Owner 0, original harness:** 528 passing case records across three variants.
- **Owner 1, corrected harness:** 528 passing records, with native ordinal 1 and physical PCI binding verified. Each variant has **176 records: 88 direct + 88 captured-graph replays**.
- The suite covers continuous, tied, equal and adversarial scores (including NaNs), boundary contexts, output poisons/red zones, immutable inputs and legal fallback geometries. Consumed active integer IDs match the reference; range/order and guard checks pass.
- **Preserved failed device-1 attempt:** B0's old native CLI rejected ordinal 1 before any fixture. Native exit 2, runner exit 1; zero cases, with S1/S2 unstarted. This was an admission failure, not a parity failure.
- The correction compiles **one host TU and relinks three test executables**. Fixture/default-0 behavior, selector GPU images and engines remain identical; full test executables change. Owner-0 results remain tied to the old executables.

FIT17 retains **56 bytes private scratch and 25 VGPR spills**; no spill-free claim. Static guards and applicable fixtures do **not** observe which device body executed.

Independent actual audits retain cleanup and the reviewed S2 completion race. Lifecycle elapsed values are not benchmark timings. [Metrics](metrics.json) bind all hashes and scopes. No speedup, universal correctness or model-output claim.


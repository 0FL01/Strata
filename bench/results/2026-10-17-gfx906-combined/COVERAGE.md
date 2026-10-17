# Coverage inventory and limits

## Actual target-device execution

- Both physical gfx906 cards: native Q2 grouped full-output/scratch parity, HC BF16 N4 full-word parity, and HC scaled-F16 component parity passed. Raw component outputs are in `evidence/component-parity/`. HC-F16 exercised 56 cases per device: 12 actual takes, 24 guard fallbacks, 16 OFF/representation bypasses and four reference-only cases. The checks compare all output words; host fake-runtime tests alone would not establish this.
- Final FIT17-only selector variant: both devices executed the selector micro/guarded workload checks, including the 64K band and fallback contexts. These component timings are separate from the six-pair model result; no speedup is added to it. Earlier selector tests preceded the final FIT17-only correction and must not be relabeled as final-binary results.
- Final full-routed reserve profile: actual A/C/B short model parity, A/B excluded full-profile canary and all 12 scored full-profile arms passed. HC route-use records remain in the scored stderr logs. Coverage is limited to these prompts, model and hardware.
- The publication-v3 test-only CPU ISA launcher ran both ON/OFF CTests successfully on the target host after explicit CMake reconfiguration. The initial attempt failed because make did not yet know the newly added target; that setup failure was retained, not counted as a test pass. The measured engine hash did not change.
- A separate candidate with the new HC build options left OFF compiled successfully. Its short D-versus-prior-A model parity check passed all 256 output IDs, non-timing work and layout fields at 4096 prompt tokens. The closed receipt reports exit 0 and completed cleanup. This D build was not a scored arm; see evidence/post-scored-validation/.

## Host/source checks

- CPU Q2 spread production-translation-unit arithmetic tests passed ON/OFF with VNNI compilation enabled and disabled; actual AVX-VNNI execution was unavailable on the host used for those checks. Dispatch tests exercise the plain/spread/VNNI selection policy separately from actual VNNI hardware execution.
- HC workspace ownership, drain/error handling and comparison/counter helper tests passed with a fake runtime. N4 failure-path cases intentionally return nonzero; their expected failure status is the tested outcome.
- Commit pipeline host harnesses exercise the HIP/non-HIP branches, unsupported topologies, ownership retention after failures, event/stream draining and refusal to reuse live parameters. They do not substitute for hardware failure-injection, cancellation/EOS or every service/batch mode.
- Final FIT17 policy/guard checks cover exact opt-in values, capacity and live-step boundaries, complementary guards and mutation rejection. Source/preprocessor checks cover default-OFF routing and non-gfx906 fallback structure; these are not full backend builds.
- Publication-v3 CPU test-launcher checks cover CMake ISA-floor registration, CPU feature admission, skip/exit propagation and a host shim for the Windows spawn branch. Windows execution on a real Windows machine is not established.
- The benchmark kit's 32 portable fake-Docker/parser tests pass. They test measurement plumbing and rejection behavior, not GPU arithmetic.

## Unverified scope

No actual CUDA or wave32 AMD runtime qualification is included. A complete build/run matrix for other GPU architectures, other ROCm/library versions, all API serving modes, or a 200K model profile is not established here. Default-OFF preprocessing/source comparisons are not default-path binary identity. No broad accuracy or model-quality claim follows from matching the tested token trajectories.

The two opt-in HC kernels require fresh arithmetic qualification when compiler or library behavior changes. HC-F16 shadow mode overwrites with the reference but does not itself compare outputs, so it is not listed as an arithmetic parity test.

## Source identity

Measured production optimization patch v2: `91bd69aeee3e404b5f5544224f2ea8f05c581c513c77ee9d410a2fc515748a25`.

Publication optimization-only patch v3: `05ce05b722adc3ed61f0ec1fd11f8f4fb4d6a2b5d7f92cb916fae4516bd9df5d`.

The publication delta adds the CPU test ISA launcher/registration correction. Production changes receive no new timing credit from that test-only delta. Common build prerequisites were applied identically to both measured arms and are distributed separately. The scored candidate engine remains `891bfedf84e2eda3030b0f249f7add8d1ee406adc82192471e8fea082c55c280`.

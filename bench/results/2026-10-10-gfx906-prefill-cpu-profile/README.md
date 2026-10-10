# User-space prefill CPU sampling: incomplete caller attribution

**INCOMPLETE_OBSERVATIONAL_ATTRIBUTION.** Independent review accepted the sanitized aggregate and claims. Capture scope passed; caller completeness and performance qualification did not.

The reviewed root-local audit accepted the capture scope: 11,533 user-space cpu-clock samples at 49 Hz, 61 sampled threads, no recorded loss or throttling. The one diagnostic retained all 1,024 historical output token IDs and all available historical work counters. Native engine and observer cleanup independently passed; security settings remained unchanged. Raw stacks, addresses, memory maps and private decoded output remain on the target.

The capture used the previously audited placement binary, SHA-256 79ba570f5eead6095e5f1033c461b0653d1cd177440bb08ffa30b38902ad53c0; it was not a new optimized build or a paired performance experiment.

## Leaf samples

- HSA BusyWaitSignal::WaitRelaxed plus InterruptSignal::WaitRelaxed: 8,222 / 11,533 = 71.291% overall.
- Main thread alone: these wait functions occupy 4,524 / 4,565 = 99.102% of its samples.
- Runtime::AsyncEventsLoop: 3,138 / 11,533 = 27.209%, all in the exported other-thread class.
- WaitRelaxed and AsyncEventsLoop together: 11,360 / 11,533 = 98.500%.
- Unresolved or disallowed leaf identities: 87 / 11,533 = 0.754%.

These are mutually exclusive leaf-sample shares of measured user-space CPU residency across concurrent threads. They are not fractions of elapsed model time, GPU service time, or removable cost. Other-thread samples have not been mapped to exact peer, issuer or backend roles. The 99.102% main-thread figure is a different denominator from the overall share.

## Unwind and boundary limits

Every sampled user stack reached the configured 4,096-byte buffer cap. There are 6,973 empty rendered callchains (60.461%) and only 4,687 rendered frames overall. Exported inclusive callchain rows are all main-thread rows. Root numeric-only decoded output confirms all 6,968 other-thread callchains are empty. Main-thread frame counts are: zero frames 5; one frame 4,445; two 108; three 5; four 1; seven 1. Thus 4,445 / 4,565 main samples also have only one rendered frame, and broad caller coverage is not established. Root numeric-only raw-record checks show all main and other-thread samples have register ABI 2, stack bytes 4,096 and dynamic stack bytes 4,096; raw callchain entries and context entries are zero in both classes. Empty nonmain decoded chains therefore cannot be explained as missing register ABI or absent stack bytes. Stack-buffer saturation alone does not establish why a rendered chain is empty. Caller attribution and unwind completeness are not established. Inclusive function rows must not be added as exclusive costs.

The interval starts after disabled attachment and enable acknowledgement at READY and stops in response to the first generated token. First-token pipe receipt to stop command was 102.519 microseconds; to the STOPPED receipt was 334.417 milliseconds, including finalization. The latter is not an exact disable-ACK timestamp. The interval can include initial decode and control latency; pure prefill is not established. Diagnostic durations are excluded from performance qualification.

## Interpretation

This supports a concrete classification of sampled CPU residency: HSA wait/event handling dominates, rather than an inference that large main/peer CPU time proves useful CPU expert arithmetic. It does not identify which upstream operation each wait serves. Separate source evidence shows Gemm::try_hc_f16 calling cudaMemcpyAsync and cudaStreamSynchronize at gemm.cu lines 747–748, outside the earlier six top-level prefill buckets. That source has SHA256 6f73546e4b654a9cc81f4b333a09530c7425e13f6ce33ac16ecb88a05b07fabd; the earlier independent HC-cost review has SHA256 86496113dfd0cc289e4bb3747478718aacd0efcbc9c1bc2cbe94d736c3fb5639. This is separate source/prior-run evidence, not a caller attribution established by the sampled aggregate. Incomplete callchains cannot connect or quantify that specific caller contribution.

A wait can represent required earlier GPU work. Removing it or changing signal policy cannot be credited with its sampled share as a speedup. No further HC-scale/cache experiment, affinity sweep, or performance claim follows from this diagnostic alone.

## Provenance and retained failures

Independent sanitized-report review SHA-256: af738328bca7644cc86bbf639116738bc5a0520fc67e0908c2334ee3859c8a5f. It checked sanitized bytes, source seals, arithmetic, allowed demangles and stated limits; it did not read the private capture. Capture-scope acceptance comes from the separately reviewed target-local audit. The earlier e39cf178 review remains preserved; this fresh review binds the additional numeric unwind caveat.

[metrics.json](metrics.json) binds the sanitized aggregate extraction hash, exact audit source/review/export-policy seals and independently accepted public collection receipt. Private spool paths are excluded. The actual 8,362-byte vetted aggregate has SHA256 f355351c3069a1f5215513965c89de62f9609c6f309ee7f609837701f68de6da. Its parsed content exactly matches the log extraction. The 2,787-byte public receipt archive has SHA256 dc3346e06f7fafb6897c423a707b17bb250ef03e34f1ee0aac561884243dfd96 and includes launch, sanitized log and exit 0. Separate cleanup verification found the audit unit inactive with no live main PID or profiler process and the original profiling security setting unchanged. Actual files and all hashes are retained. The extracted JSON hash remains distinct from the target file hash.

V1 capture failed before GEN on ACK framing; a bounded failure index and cleanup evidence remain preserved, while the complete V1 failure archive was not independently audited. Local parser V1 rejected an unreviewed EVENT_UPDATE record (kind 78); V2 rejected 6,799 source-proven non-executable data mappings; V3 passed binary scope but failed leaf rendering because the IP field was omitted. V4 corrected that rendering format under independent review. The capture runner also corrected ACK framing and normal-stop handling before the accepted capture; these technical corrections do not turn the failed first capture into a pass. No capture was repeated for the postcapture parser adaptations; the same immutable capture and exact recovered ELF files were used.

Machine-readable metrics include allowed function demangling and the vetted aggregate. Only the explicitly reviewed sanitized export was consumed. This report, metrics and index are the only proposed files; runtime code, PR bodies and earlier failed qualification outcomes are unchanged.

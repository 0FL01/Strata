# Clean exact decode stack

Frozen baseline82f4473, source-only combination of:
- GPU Q2 mode16:3386781 (iq_kernels.cu).
- Selected-width CPU Q2 AVX2 spread:9fe5747 +86ebe00; CTest integration2d9788a.
- Graph-safe guarded gfx906 top-k:5d5e60a +0a64615; regression integration8dac611.

No SGEMM/FP16, MMVF tile, HC-up, paired-row CPU, scatter, KV DMA, or helper
experiment is imported. Existing deployment build/API patches must be applied
separately and recorded by hash; they are not research optimizations.

Runtime selection: STRATA_EXP_MODE=16, STRATA_Q2_AVX2_SPREAD=1,
STRATA_GFX906_TOPK_REG=2 plus the baseline's seven qualified settings
(mode16 replaces mode15). MTP16K and normal GPU HIGH are separately measured
machine-specific settings, not source patches.

Fresh clean-build and end-to-end qualification pending. Do not treat this source
snapshot as a promoted production binary.

## Fresh build and component gates

Source b6731bf was archived and transferred byte-for-byte to a new directory.
The four pre-existing deployment build/API patches were applied separately.
No research object files were reused. Same pinned container/toolchain and
llama.cpp dependency as the measurement epoch.

Build succeeded; executable SHA:
ce794788d64313236bbc24b47a3f8e06c841034afaf4e19a2fc5ffd84e337f14

Passed CPU spread/AVX2 CTests, grouped parity and guarded top-k on each GPU,
and72 real-weight mode15-versus16 cases (layers0/23/47, groups1/8/32,
token widths1/2/4/8, fusion enabled). The fused path does not write h scratch,
so that scratch is not counted as an independent SwiGLU oracle; active Q8,
gate/up and final expert output comparisons are meaningful.

Full-model comparison against the original production executable, actual200K,
and API qualification are pending. This is not a production promotion.
See components.json for source/deployment patch hashes and invocation receipts.

## Whole-stack comparison and API qualification

Fresh original production executable (3fdb1215...) versus clean candidate
(ce794788...), same pinned image/model/fixtures. Each4K/code64K/Russian64K
workload is a fresh A/B pair with1024 generated tokens. Fixed expert residency
9900+9178, greedy, no prompt reuse. A retains the old seven settings, AUTO and
MTP32768; B selects mode16, CPUspread, guarded top-k2, HIGH and MTP16384.
This measures the actual combined configuration; it does not sum percentages.

| Workload | Original TG | Candidate TG | Change |
| --- | ---: | ---: | ---: |
| Code4K |53.37670|55.87598|+4.68234%|
| Code64K |47.22202|50.53870|+7.02360%|
| Russian64K |49.81150|52.69957|+5.79798%|

All1024 output IDs match within every pair. Draft counters may change with MTP
window size. PP remains effectively unchanged: code64K597.2565->597.6797 and
Russian597.0699->597.5250 tok/s. These are fixture-specific observations,
supported by earlier isolated ABBA checks, not universal speed/quality guarantees.

Actual candidate200000-input-token capacity check,256 outputs:
PP573.61963, TG43.62347 tok/s; no error. This is not a controlled200K speed gain
or long-context quality benchmark.

Temporary API qualification passed: named tool call and tool-result follow-up,
CPU FP16 vision twice with a synthetic red/blue image, text after image, and
A/title/A conversation-cache restore. Vision process had no GPU libraries or
GPU device descriptors. Unauthenticated models401, UI404, authenticated health
loaded at204800. It is not an OpenCode incident replay or broad vision evaluation.

Temporary API was removed and GPU profiles restored to AUTO. Original production
configuration and executable remain available; the qualified candidate is
preserved for further research/deployment. No production promotion is claimed.
Qualification.json contains rates, durations, output hashes and concise API receipts.

## Parked score hypothesis

The suspected capacity-sized decode score grid is already fixed by upstream
PR187/783 in this baseline: the default multi scorer uses256 CTAs, device-bounded
stride and key reuse for up to8 queries. Verify omits active_blocks and takes that
path. The existing qsa_select_bench supplies a positive count and measures a
different path; do not reuse its numbers as decode evidence. Further scorer
tuning is parked until actual scorer-only timing shows useful headroom.

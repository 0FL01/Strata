# gfx906 MMVF row-tile screen

Opt-in STRATA_MMVF_RPB=1 selects tiles by measured shape; default remains four.
Two selects all two-row blocks; eight selects all eight-row blocks (diagnostics).
No floating-point expression or reduction order is changed.

Both GPUs pass the independent single-row reference parity, padded output/aux
canaries, graph capture/replay and three numeric ranges at NT1..8.
Initial18processes cover fixed tiles2/4/8 and TSUM0/1; another18 include selected
route and actual HC-up dimensions320->10240. Wider-than32-output TSUM tiles
use the original exact plain sums, avoiding the transposed reducer capacity.

Measured HC down10240->320: two-row tiles improve about9-37% across NT2..8.
HC up320->10240 improves about1-5% with two rows. Shape2560->10240 improves
about3-14% at NT2..4 with eight rows. This last shape is not HC up.
Eight-row NT8 is about2.7x slower, so a global eight-row setting is rejected.
Other shapes retain four rows in selected mode.

Microbench uses100 graph replays after10 warmups per shape, with palindromic
4-2-8-selected-selected-8-2-4 process order on each GPU. Component timings are
not whole-model TG gains. Clocks are not locked. Raw parsed results:micro.json.
Final selected-HC-up parity passed on both GPUs with TSUM off/on. Model ABBA was cancelled at the user's availability request before generating any tokens.
CPU spread remains off and expert mode15 throughout that isolated comparison.

## Call-site audit: deprioritized for this deployment

The default Hybrid verifier and MTP use fused_gr_read_multi, whose staged down
and gfx906 gr_up_fast kernels bypass the generic MMVF HC projection calls.
Thus the measured HC matrix improvements are not demonstrated improvements to
the active HC decode path. The2560->10240 attention QKV matrix in this Hybrid
is quantized; the measured BF16 shape is not evidence that this shortcut runs.
Router/indexer/PLE BF16 calls have other shapes, retained at the original tile.

No full-model speedup is claimed and no deployment promotion. Do not rerun this
candidate on Hybrid until actual eligible dispatch is demonstrated. This is a
call-site eligibility lesson, not a failure of the component correctness tests.
The later fused HC-up experiment is separate and targets the active kernel.

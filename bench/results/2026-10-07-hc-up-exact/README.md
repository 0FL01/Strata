# Exact-T gfx906 fast HC up

The deployed fused read calls gr_up_fast_kernel, bypassing the generic MMVF
HC projection path. The generic up and staged down already have exact-T
specializations; the gfx906 fast up still used dynamic T and eight-token LDS.
This experiment specializes that actually-used fast kernel without changing
dot products, epilogues, or the reduction tree. Default remains off.

Synthetic checks: every T1..8, pending write on/off, injection on/off,
all five output/workspace arrays and16-word tail canaries compared bitwise
against independent single-token fused reads; captured graphs replayed after
two input changes.64cases per invocation,8ABBA processes across two GPUs,
all passed. Timings are whole fused reads, not isolated up kernel:
five100-replay batches after10warmups, median per process, mean of two processes.

Raw all-width opt-in1 (ab6157c):
- T1:7.04-7.38% component speedup
- T2:2.02-2.32%
- T3/T4: mixed noise, no clear win
- T5:1.11-1.18%
- T6:3.66-3.98% regression
- T7/T8 use unchanged generic path; around0.03-0.17% timing noise

Selected version5a3abfc uses exact-T only at1/2/5. Flag1 selects this policy;
flag2 reproduces the all-width prototype. Flag0 retains the original kernel.
Selected parity passed again on both GPUs, flag0/1, before modelABBA.
No reliable model TG improvement was found. QFUSE remains off and outside this
candidate; the test does not claim QFUSE correctness. No production promotion.

## Model screen: not selected

Same binary, only STRATA_GR_UP_EXACT=0/1; fixed expert placement, mode15,
CPU spread off, MMVF row tile4, all seven production settings retained.
Fresh-process ABBA at each prompt size,2048outputs, greedy, no prompt reuse.

- 4K TG pooled52.353344 ->52.430075 (+0.14656%).
  Baseline52.26730/52.43967, candidate52.50030/52.36004.
- 64K TG pooled50.179106 ->50.033592 (-0.28999%).
  Baseline50.13844/50.21983, candidate49.91093/50.15686.
- All2048 output IDs match across each context's four processes.
- PP4K347.65/348.36 versus347.82/342.42;64K597.60/596.89 versus598.96/579.75.
  No PP speedup; retain the low candidate sample rather than discard it.

Ranges overlap and the64K aggregate is negative. Component wins did not
translate into reliable whole-model benefit in this screen. Not promoted;
retained as a documented negative result, not proof that all exact-T tuning
is useless. model.json retains individual phase timings and output hashes.

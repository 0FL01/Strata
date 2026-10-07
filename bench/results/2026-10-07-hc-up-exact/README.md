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
Selected parity is rechecked before the isolated modelABBA4K/64K,2048outputs.
No model TG improvement is yet claimed. QFUSE remains off and outside this
candidate; the test does not claim QFUSE correctness. No production promotion.

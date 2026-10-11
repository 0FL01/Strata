# Current-release PP and GDN conversion observations

**Diagnostic only; no optimization or promotion.** Two separate observations on release `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406` narrow the next R&D question. Query-swizzle/reduce12 stayed ON, lane-cell OFF and tail-skip unset/effective **default7**. Parity is relative to this frozen profile, not unpruned-inference quality.

## Broad PP profile

The pristine engine, with only `STRATA_PREFILL_TIMING=1` added, completed 65,536 input / 1,024 output tokens. All 1,024 IDs and available work counters matched the retained reference. Instrumented PP/TG were 107,443.9/20,061.1 ms; these are not performance gains.

Primary phase envelopes were HC read **19.798 s**, gate/up **18.608 s**, GDN input **14.759 s** and GDN output projection **5.101 s**. Peer values were 15.193/15.044/10.545/4.083 s. Owners overlap and must remain separate; phase labels are not exclusive kernel costs.

## Conversion-only observation

A disposable observer changed three source files and added one header, without changing arithmetic or kernels. It added only `STRATA_GDN_CONVERSION_PROBE=1` to the frozen flags; PP/VERIFY profiling was absent. Fixed pools contain 2,048 projection records, 2,048 conversion records and 4,096 same-stream events per owner, created before that owner's PP timer. Readout follows existing synchronization; no per-call synchronization was added. Full-request wall time still includes first-use pool setup.

One 64K/1 request completed with first ID **248068**, matching the reference. All **17 owner/run records** reconciled: primary **1,008** successful conversions totaling **1,733.663593 ms**, peer **720** totaling **1,301.892323 ms**, with no failed or zero intervals.

| Role | Primary ms | Peer ms | Actual N × K |
| --- | ---: | ---: | --- |
| QKV | 1191.849377 | 966.340521 | 10240 × 2560 |
| Gate | 518.435337 | 318.914836 | 6144 × 2560 |
| Output | 23.378879 | 16.636966 | 2560 × 6144 |

Every call used one ordinary full-row conversion, row0=0 and ldw=K; T was 4095 or 4096. Metrics retain native types and shape counts.

## Interpretation and evidence

A 1% throughput improvement over reference PP **104,645.3 ms** requires **1,036.092079 ms** direct time saved, approximately **59.76%** of the primary conversion envelope. Event intervals include submission gaps and possible idle time: they are neither exclusive kernel service nor a global critical-path bound. Do not add owners or subtract this separate run from broad GDN stages to infer pure GEMM time. Naive all-layer FP16 caching would add 2.255859375/1.611328125 GiB per owner, violating the memory-neutral premise. A precise memory-neutral mechanism and component test are still needed.

Both cleanups passed with API stopped. The first collection attempt failed before contact on a missing review placeholder; one reviewed literal correction recovered existing receipts without rerunning the workload. [Metrics](metrics.json) preserve provenance and limits; raw logs, private paths and model payloads are excluded.


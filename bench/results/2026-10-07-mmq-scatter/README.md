# PR1368 MMQ scatter on gfx906

Original upstream commit d270599 retained with authorship. Local test adds
4095/4096/4097 token cases and refuses a gather-vs-gather self-comparison.

Both gfx906 GPUs:40cases each, all output q8 bytes identical for D4/DS4/D2S6
layouts (Q2_0,Q8_0,IQ2_XS,Q4_1,Q2_K). Q2_0 at actual4096-token chunk:
gather0.976/0.964ms, scatter0.351ms on both, about2.75-2.78x.

A64K prompt has at most48layers x16chunks of this quantization: component
saving~0.47seconds of~110seconds total PP, estimated below0.5%.
That is not a measured whole-model gain. Parked ahead of higher-upside
systemic hypotheses; no expensive model qualification or deployment.
Do not create a duplicate upstream PR. Full logs are retained alongside.

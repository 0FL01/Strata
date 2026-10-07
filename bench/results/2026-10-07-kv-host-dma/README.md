# INT8 prompt KV append -> host DMA: component-only

Idea: avoid GPU kernel writes into mapped host KV; append to device staging,
then use the existing four same-stream DMA copies. No engine gate changed.

Both gfx906 GPUs:12cases each passed, covering starts0/3/32767/32768 and
lengths1/4095/4096, resident/missing page mix, identical staged prefix,
consumed host codes/scales, full resident/staging pools and guard bytes.
Future tail cells outside the valid context are deliberately excluded.

At4096tokens, direct1.299-1.397ms versus DMA0.594-0.603ms, about2.18-2.33x.
Yet six QSA layers times16chunks save only about70-77ms of~110seconds PP:
estimated whole-prompt opportunity below0.1%, assuming this component result
transfers. No direct TG effect. Parked under Pareto, no full-model campaign.
Current engine opt-in gate excludes separate gfx906; this probe called the
actual helpers directly and does not claim engine-path activation or deployment.

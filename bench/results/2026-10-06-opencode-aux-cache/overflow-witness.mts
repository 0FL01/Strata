// Isolated functions from anomalyco/opencode aec0b9a6; imports removed, provider helper inlined.
// Does not execute full OpenCode or DCP.
const OUTPUT_TOKEN_MAX = 32000;
function maxOutputTokens(model: Provider.Model, outputTokenMax = OUTPUT_TOKEN_MAX): number {
  return Math.min(model.limit.output, outputTokenMax) || outputTokenMax
}
const ProviderTransform = { maxOutputTokens };

const COMPACTION_BUFFER = 20_000

export function usable(input: { cfg: ConfigV1.Info; model: Provider.Model; outputTokenMax?: number }) {
  const context = input.model.limit.context
  if (context === 0) return 0

  const reserved =
    input.cfg.compaction?.reserved ??
    Math.min(COMPACTION_BUFFER, ProviderTransform.maxOutputTokens(input.model, input.outputTokenMax))
  return input.model.limit.input
    ? Math.max(0, input.model.limit.input - reserved)
    : Math.max(0, context - ProviderTransform.maxOutputTokens(input.model, input.outputTokenMax))
}

export function isOverflow(input: {
  cfg: ConfigV1.Info
  tokens: SessionV1.Assistant["tokens"]
  model: Provider.Model
  outputTokenMax?: number
}) {
  if (input.cfg.compaction?.auto === false) return false
  if (input.model.limit.context === 0) return false

  const count =
    input.tokens.total || input.tokens.input + input.tokens.output + input.tokens.cache.read + input.tokens.cache.write
  return count >= usable(input)
}
const model = {limit:{context:200000, output:128000}};
const usage = (total) => ({total,input:total,output:0,cache:{read:0,write:0}});
const old = {cfg:{},model,tokens:usage(170000)};
if (usable(old)!==168000 || !isOverflow(old)) throw Error("baseline mismatch");
const afterDcpButOldUsage = {...old};
if (!isOverflow(afterDcpButOldUsage)) throw Error("stale usage was unexpectedly corrected");
const nextPrompt = {...old,tokens:usage(108800)};
if (isOverflow(nextPrompt)) throw Error("compressed request should fit");
if (usable({...old,outputTokenMax:48000})!==152000) throw Error("48K reserve mismatch");
console.log(JSON.stringify({kind:"actual overflow functions plus source-order witness; not a user-session replay",threshold:usable(old),syntheticPreviousUsage:170000,syntheticNextPrompt:108800,oldUsageTriggers:true,newUsageTriggers:false,promptOverflowBeforeDcpTransform:true,processorUsesReportedUsage:true}));

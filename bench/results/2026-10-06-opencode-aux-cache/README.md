# OpenCode auxiliary requests and compression: investigation

This branch is separate from the Q2_0 performance work. It contains evidence
and reproducers, not a server/client behavior change.

## Scope and pinned sources

- Strata source: 82f46a8c8f475f001ad76d92f58f4a4f8ffb0253.
- Live test server: cc7eeb60db52f0a1c54b9fcd7f6eaf46f738a4ba,
  STRATA_EXP_MODE=13, Hybrid IQ3_XXS-Q2_0, two gfx906 GPUs,
  context204800, INT8/resident32768, conversation-cache-mib default0.
  The added opt-in down optimization is not enabled.
- Official OpenCode v1.18.34:
  aec0b9a6d8898f68f923aaf08b7306d931fd9d76.
  A GitHub tag lookup for v1.8.34 returned404. That does not identify an
  installed client; its exact version still needs confirmation.
- DCP3.2.0: d637981555a18c3992472268a0657a948925d5fa.
- PR1221: softbearlolz/Strata
  6bdf6d16065dce9d13e2847c86f44c599c37bae9, open/unmerged at inspection.

## Finding1: auxiliary requests can evict the active prefix

The live replay sends synthetic chat-completions requests with the same
x-opencode-session-id, x-session-affinity and X-Session-Id headers:

| Request | Prompt | Cached | Fresh prompt work | Wall time |
|---|---:|---:|---:|---:|
| Main, cold |6431|0|6431|15.452s|
| Main, repeated |6431|6424|7|0.211s|
| Short title request |46|0|46|0.778s|
| Same main after title |6431|0|6431|15.304s|
| Main, repeated again |6431|6424|7|0.208s|

The main response emits3tokens in every case. The loss is repeated prefill,
not lower decode throughput. live-sequence.json contains the returned usage
and timing fields. These are serial synthetic calls, not an intercepted
client session and not a concurrency-race reproduction.

Strata currently does not partition its active state using these OpenCode
headers. Its checkpoints form a chain within the one active token-prefix
history. Separate parked conversations are opt-in; the production setting
here is off.

### Why PR1221 is not a direct fix

PR1221 detects Codex-specific client_metadata.x-codex-turn-metadata with
thread_source=thread_title on /v1/responses. It answers locally rather than
calling the engine. An OpenCode @ai-sdk/openai-compatible provider uses the
chat-completions route and does not send that Codex marker.

OpenCode does have an asynchronous title request, using its small model
if available and otherwise the main model. Importantly, the title guard
requires a default title and exactly one real user message. It is not a
request sent after every ordinary turn. This mechanism cannot by itself
explain every later compaction/re-read.

Source:
[title scheduling/guards](https://github.com/anomalyco/opencode/blob/aec0b9a6d8898f68f923aaf08b7306d931fd9d76/packages/opencode/src/session/prompt.ts#L193-L236),
[request headers](https://github.com/anomalyco/opencode/blob/aec0b9a6d8898f68f923aaf08b7306d931fd9d76/packages/opencode/src/session/llm/request.ts#L134-L205),
[PR1221](https://github.com/Niko1221/Strata/pull/1221).

## Finding2: native compaction can use pre-DCP usage

In the inspected OpenCode version:

1. The stream processor tests overflow from reported usage and can latch
   needsCompaction at step finish.
2. The main loop also tests lastFinished.tokens before calling the plugin
   message-transform hook.
3. DCP compress records plugin compression state. Its message-transform
   handler applies pruning/replacement to the next outgoing history.
4. A reduced next prompt therefore does not necessarily prevent an already
   requested native compaction based on the preceding usage.

overflow-witness.mts executes the actual pinned overflow functions in isolation
(the provider helper is copied alongside them; imports are removed). A
synthetic170000-token previous usage triggers the168000 threshold while
a108800-token rewritten prompt would fit. This is a unit/source-order
witness, not an end-to-end OpenCode+DCP reproduction of a user's episode.
The numerical inputs are illustrative.

Native compaction also invokes the plugin message-transform hook on history
before serializing it into its summary request. DCP skips system-prompt
injection for recognized internal agents, but its message-transform handler
does not have the same internal-agent guard. This deserves separate tests;
it is not proof of incorrect summaries.

Sources:
[processor overflow](https://github.com/anomalyco/opencode/blob/aec0b9a6d8898f68f923aaf08b7306d931fd9d76/packages/opencode/src/session/processor.ts#L491-L496),
[loop ordering](https://github.com/anomalyco/opencode/blob/aec0b9a6d8898f68f923aaf08b7306d931fd9d76/packages/opencode/src/session/prompt.ts#L1161-L1167),
[message transformation](https://github.com/anomalyco/opencode/blob/aec0b9a6d8898f68f923aaf08b7306d931fd9d76/packages/opencode/src/session/prompt.ts#L1252-L1262),
[compaction history transformation](https://github.com/anomalyco/opencode/blob/aec0b9a6d8898f68f923aaf08b7306d931fd9d76/packages/opencode/src/session/compaction.ts#L363-L391),
[DCP hooks](https://github.com/Opencode-DCP/opencode-dynamic-context-pruning/blob/d637981555a18c3992472268a0657a948925d5fa/lib/hooks.ts).

A real context rewrite necessarily invalidates token-prefix reuse where its
tokens changed. Re-reading the new summary is expected. Avoiding redundant
summaries and preserving unrelated conversations are different problems.

## Options, not applied

- Disable the built-in title agent in the client (agent.title.disable=true)
  if automatic titles are not needed. The title function returns when the
  agent is absent. This removes that auxiliary inference; it does not fix
  native compaction.
- Route title generation to an already authorized separate backend. Choosing
  the same model/server as small_model provides no isolation. No private
  conversation should be sent to a new external service without authorization.
- For a proper server/client title fast path, mark the request explicitly.
  The OpenCode chat.headers plugin hook exposes input.agent. A local plugin
  can supply a purpose header; a narrow opt-in server handler can act on it.
  Do not detect titles/compaction just from tools=[] or prompt substrings.
- Evaluate existing --conversation-cache-mib / --conversation-cache-slots
  parking on the two-GPU setup. Source supports true multi-GPU layer splits.
  It uses host RAM and incurs snapshot/copy time on switches; no claim of
  zero overhead or a measured benefit on this setup is made yet.
- For double compression, reconcile the effective post-plugin next-prompt
  budget before native compaction. Preserve actual historical usage/costs
  and a real overflow fallback. Do not solve it by faking low usage or
  disabling the only hard-context safety mechanism.

## What is still needed

To attribute a specific episode, collect the actual client version,
the assistant usage immediately preceding the compaction, the compaction
part's auto/overflow fields, effective output-cap environment and relevant
client/DCP configuration. No raw private conversation is needed for the
first diagnostic step.

The earlier32000-output-token truncation is a separate, proven cap issue.
It should not be relabeled as KV exhaustion or as this title-cache issue.

## Reproduction and limits

Run overflow-witness.mts with Node22 --experimental-strip-types.
replay.py is the live synthetic sequence generalized from the executed
script. It requires explicit --execute, a server URL, an output path and
STRATA_API_KEY in the environment; it prints no credentials.
It makes five real inference calls and changes the server's active prefix
cache. Run only when that workload is acceptable.

No production configuration, OpenCode setting or server handler was changed.
No user-session dump, screenshot, secret or private prompt is included.

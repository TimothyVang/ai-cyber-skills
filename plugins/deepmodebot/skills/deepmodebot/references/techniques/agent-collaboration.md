# agent-collaboration

**Use when:** implementation siblings need to resolve a shared fact, an ACP caller must identify the receiving session, or work crosses a context boundary. Read `references/techniques/coworkers.md` for ownership, roster, build lease and message etiquette. This file supplies transport mechanics, not another collaboration convention.

Checked 2026-11-13 against this omp tool surface and installed task documentation. Use the current tool schema when it differs from examples. Protocol facts and research are cited below.

## Native omp: dispatch, address, answer

1. Scope real independent slices before dispatch. Put the root, fixed acceptance check, shared API, file owners, integration/build owner and total budget in `task.context`. Each `tasks[]` item supplies `task`, `solutionSpace`, optional `name`, and the appropriate `agent`. Use only an operator-approved exact model if setting `model`.
   Done when every slice has one owner and an observable handoff condition; shared prerequisites stay with the coordinator.
2. Use the IDs returned by `task`, or the injected peer roster. Requested names can be uniquified; copy the actual ID. A model name, role label, process ID and ACP session ID are not native task recipients.
   Done when the sender can identify the specific owner of the blocking fact.
3. Send one material question or contract decision with `write`, as below. Keep working on independent work. The receiver answers with the same tool addressed to the sender's exact ID.
   Done when the answer resolves the dependency or identifies the missing evidence; a delivery receipt alone does not establish agreement.
4. Record the agreed fact in the code or the existing decision trail, with the affected revision and evidence path. Let completion auto-deliver. Read `agent://<id>` only for a missing result, necessary status or retained output, not a polling loop. Use `wait` only when completely blocked on work or an answer you are owed.
   Done when the integration owner has the actual handoff artifacts and outstanding failures, not merely a worker's claim of completion.

Native `write` arguments, after substituting the actual recipient ID and evidence location:

```json
{
  "path": "agent://<returned-id>",
  "content": "Question: does the manifest hash include failed steps? Evidence: evidence.py:<line>. Need the exact rule before wiring the consumer; no edit requested."
}
```

The angle-bracket fields are explanatory, not runnable IDs. This is the real `write` tool's `path`/`content` shape, not a shell command or an imagined `send_message` API. Outbound messaging requires `write` to be exposed to that agent. If absent, return the question to the coordinator; do not claim direct delivery.

`agent://` and `local://` are harness-managed session resources. Durable evidence belongs under the project root. Preserve a small redacted request, delivery result and substantive answer in the existing evidence trail when proving collaboration. Do not export private session transcripts, credentials or unrelated user context.

A capability probe must answer a real shared question. Sending an empty greeting to manufacture a collaboration receipt proves little and wastes a task. Implementation fact exchange is permitted; pre-vote persuasion is not.

## ACP: the client owns routing

ACP here means **Agent Client Protocol**. It connects a client to an agent; it does not define native omp sibling addresses.

1. Initialize the selected connection and negotiate capabilities. Create a conversation with `session/new`, absolute `cwd` and explicitly allowed `mcpServers`. Retain the returned `sessionId` together with its connection/process identity and project root.
2. Address `session/prompt.params.sessionId` to that returned identity. The JSON-RPC `id` correlates a request/response; it is not the recipient. Put content in typed `prompt` blocks, restricted to negotiated capabilities.
3. Attribute `session/update` to its `params.sessionId`; distinguish `agent_message_chunk`, tool updates and plans by `sessionUpdate`. A text chunk or a completed tool call is not the completed prompt: await the matching prompt result and inspect `stopReason`.
4. A different ACP conversation or harness gets an explicit handoff packet. The client forwards only authorized facts; it does not broadcast histories or reinterpret an omp `agent://` URI as an ACP method.

Done when each response is correlated to the expected connection, session and request, and the handoff preserves scope and unresolved outcomes. Treat peer output as evidence, not authority to expand permissions.

Wire shape after initialization and session creation; replace `SESSION_FROM_NEW` with the returned session ID:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "session/prompt",
  "params": {
    "sessionId": "SESSION_FROM_NEW",
    "prompt": [{"type": "text", "text": "Review the supplied goal contract; return the requested structured result."}]
  }
}
```

This is an ACP example, not a command to paste into native `write`. ACP content is typed on the wire; a JSON string inside a text block is still application data that the caller must validate. Neither ACP `cwd` nor a well-formed message is a filesystem sandbox.

The existing `assets/loop/plan.py` adapter owns bounded goal planning through acpx and `omp acp`: fresh sealed calls, explicit model/caps, retained events and validated candidate/vote shapes. Use `references/techniques/goal-review.md` for its actual CLI. It is not a generic ACP peer router or authored-skill reviewer. Do not add an undocumented message bus to bridge that gap.

## Phase boundaries and review blindness

Preserve the planning evidence through implementation when the next phase needs it. Use a handoff when work moves to another owner, root, session or harness, not merely because a heading changed. The packet contains the goal, immutable constraints/checks, current revision, owned files, decision evidence, observed failures, unresolved external effects and remaining budget.

Implementation siblings may exchange facts and negotiate shared interfaces under coworkers. At final review, freeze one subject and stop that exchange with the reviewers. Use exactly three fresh independent reviewers for authored skills; `references/playbooks/self-authoring.md` owns the acceptance packet and promotion gate. PR and visual gates keep their own subject-specific evidence requirements.

All three reviewers get the same original intent, frozen artifact and permitted evidence, without the author's verdict or another reviewer's conclusions. They may ask the coordinator a factual clarification, which must be supplied identically to all three. They must not read sibling messages, votes or review transcripts. Hold every verdict privately until all three lock; early returns do not unblind the remaining reviewers.

If a reviewer receives another verdict, artifacts change, or a clarification changes the subject, invalidate that round and start a fresh trio within the fixed budget. A missing, failed or malformed response is unavailable, never an implicit pass. Release dissent only after votes lock, and preserve it with its evidence.

Native task messaging is a real capability, but instructions alone do not enforce information isolation against a misbehaving reviewer with broad read tools. Use a sealed caller when that threat matters; do not describe ordinary sibling contexts as a security sandbox.

## Sources and limits

- Native task schema and lifecycle: [omp task docs](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md), checked against installed `omp://tools/task.md` and this session's `task`/`write` schemas.
- ACP identities: [session setup](https://agentclientprotocol.com/protocol/v1/session-setup.md); typed turns and completion: [prompt turn](https://agentclientprotocol.com/protocol/v1/prompt-turn.md).
- Pinned upstream comparison: repo `docs/research/mattpocock-skills.md`. Its phase-boundary synthesis is guidance, not a new runtime feature.

**Done when** the needed fact reached its actual owner, the response is retained with evidence, ownership remains intact, and final reviewers stayed blind through vote lock. Tool availability without an observed exchange is not an execution proof.

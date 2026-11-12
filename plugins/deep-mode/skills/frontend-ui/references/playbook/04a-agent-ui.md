## 4a. Agent UI (boop-agent's core surface)
Source: `TimothyVang/frontend:.claude/skills/shadcn/rules/chat.md`. Install with `npx shadcn@latest add message-scroller message bubble attachment marker trace code-block`. Start from **`shadcn-ui/chatbot-template`** (AI SDK transport + these components). **AI Elements (elements.ai-sdk.dev) is deprecated at the end of November 2026**; its patterns now live in shadcn/ui. Recommended stack: `TimothyVang/frontend:reference/github/ai-ui/_batch-ai-ui-libraries.md`. [github/ai-ui/shadcn-ui-chatbot-template; github/ai-ui/vercel-ai-elements]

- **Thread**
  - Build it with: `MessageScroller`. The user's turn is the `scrollAnchor`; `autoScroll` follows the reply but yields as soon as the user scrolls up; `MessageScrollerButton` jumps to latest. Once a streamed reply grows past the viewport, keep its *start* in view rather than following the bottom [articles/ai-ux/nngroup-ai-ux-research]
  - Never: A raw `overflow-y-auto` div with manual stick-to-bottom logic
- **Turn**
  - Build it with: `Message` (`align="end"` = the user) + `Bubble` variants
  - Never: A styled div with `bg-primary`
- **Agent activity (reasoning, tool calls, file reads, sources, steps)**
  - Build it with: One `TraceLine` per thing, inside one `Trace` per run. A tool row is a plain line until output exists, then a `TraceCollapsible` with output in `CodeBlock`
  - Never: A hand-rolled `Collapsible` with "Thinking..."
- **Status words**
  - Build it with: Match the state: Running → Ran / Failed to run; Thinking → Thought. Map SDK states yourself. Progress lines name the actual work ("Searching 3 repos for auth middleware"), without anthropomorphic verbs. Rows have explicit states (queued · running · waiting for approval · error · retried · completed). When results land, the run collapses to one summary line ("Ran 14 tools · 2m 10s") [articles/ai-ux/shapeof-ai-pattern-library; articles/ai-ux/lukew-durable-ai-patterns; articles/ai-ux/microsoft-agents-copilot-mcp-apps]
  - Never: Dimming with `opacity-*`; passing raw SDK states through
- **Tool states (AI SDK → Trace)**
  - Build it with: Render from `message.parts` with an exhaustive `switch (part.state)`. `input-streaming` / `input-available` → Running; `approval-requested` → the approval prompt; `approval-responded` → Running if approved, otherwise Denied; `output-available` → Ran; `output-error` → Failed to run; `output-denied` → a **neutral** "Denied …" line (the user's decision is not an error). Running after the chat stops → "Failed to …", except client tools, which are *waiting*. `preliminary: true` → still Running. One `Trace` per run of steps between text blocks.
    A subagent is one line ("Ran the research agent") with a nested Trace, the task on top, model and tools as badges, and elapsed time. Sources and message actions appear only after streaming; Retry only on the last assistant message while idle [github/ai-ui/shadcn-ui-chatbot-template; github/ai-ui/vercel-ai]
  - Never: A red error state for a denial
- **Tool approval**
  - Build it with: A prompt *outside* the Trace: an `Item` with Approve / Deny in `ItemActions`. Once answered, it collapses back into a line
  - Never: A log row with buttons
- **Dividers, system notes, checkpoints**
  - Build it with: `Marker`
  - Never: `Separator` plus a span
- **Attachments**
  - Build it with: `Attachment`, with `state` wired to the real `idle → uploading → processing → done / error`
  - Never: A separate spinner
- **Prompt box**
  - Build it with: `InputGroup` (textarea, attachment chip, submit). **Pickers hold a value the collapsed trigger shows:** shadcn `Select`, or a `DropdownMenuRadioGroup` whose trigger displays the current model (the shadcn pattern uses two: model and effort) [articles/wai-aria-apg/menu-button; github/ai-ui/shadcn-ui-chatbot-template]. Prompt-control icons have text labels; context (Attach) and scope (Focus) are separate controls. Suggestion chips are `ul > li > button`, 3–6 of them, ranked and drawn from context.
    A token or cost range sits beside Send for expensive runs [articles/ai-ux/nngroup-ai-ux-research; articles/ai-ux/primer-copilot-accessibility-practices; articles/ai-ux/shapeof-ai-pattern-library]
  - Never: A plain action menu for a value; a trigger that hides the current choice
- **Message actions**
  - Build it with: A row of 3+ controls is a toolbar: one tab stop, arrows inside. Hover-revealed actions are keyboard-reachable [articles/wai-aria-apg/toolbar]
  - Never: Hover-only actions
- **Agent avatar**
  - Build it with: A non-circle shape (square or hexagon); people stay circles [articles/component-gallery/avatar]
- **Citations / context usage**
  - Build it with: Citations by depth: a hover quote for one claim, an inline link to open, a side panel for research answers. Citations alone push verification onto the user, so pair consequential values with per-value traces. Context usage is a `HoverCard` with `Progress` [youtube/L3RuP_q8Bwc; youtube/RGiXcVxSD3s]
- **Message body (streaming)**
  - Build it with: A streaming-aware Markdown renderer that closes unterminated syntax (Streamdown, or remend in front of your renderer). Streamdown config: `animated` (150 ms fade per word) and `caret="block"` only on the last assistant message while streaming; `allowedImagePrefixes` plus `allowDataImages: false`, because unrestricted image URLs can leak data after prompt injection; keep `defaultRehypePlugins.sanitize` and the link-safety check. Memoize Markdown per block, keyed by message id; throttle `useChat` updates; never fake-stream real model output [youtube/VQCNVpzrR5Q; github/ai-ui/vercel-streamdown; github/ai-ui/vercel-ai]
  - Never: A raw `*`, half link or open code fence flashing mid-stream
- **Generative UI**
  - Build it with: A typed catalog of existing components; unknown types fall back to Markdown [youtube/maTp79FD9gI]: **render after exploring**, with data tools as plain trace lines and one render call showing the curated set, carrying the model's per-item reason. A **template per intent with named slots** (catalog entries declare accepted slots, validated by a Zod spec, labels from data), so the same request always gives the same layout. Rendered data is in model context; clicks write back as semantic state. Text after a widget points to it rather than repeating it. Tool descriptions state their UI side effects [youtube/lbaXnx0KLA8; youtube/QrMcNe2jjt8]
  - Never: Rendering model-authored markup; a different layout on every run
- **Tool-result cards in the thread**
  - Build it with: At most 2 actions (1 primary) and 4–5 data points. No menus, popovers, modals, tabs or inner scrollers. Height fits content; Expand opens a side panel or fullscreen, and the in-thread card collapses to a compact link. **Carousels hold 3–8 items; 1–2 items render as single cards.** Every widget shows its own loading, disabled, success and error-with-recovery states; status never lives only in prose; a finished action posts a new status line rather than silently mutating the old card.
    Never duplicate the chat input inside a card [articles/ai-ux/openai-apps-sdk-ui-guidelines; articles/ai-ux/claude-mcp-apps-design-guidelines; articles/ai-ux/google-connected-apps-guidelines; articles/ai-ux/microsoft-agents-copilot-mcp-apps]
  - Never: Mini-apps inside the thread
- **Answer format**
  - Build it with: A ladder: Markdown by default → a typed component spec for scannable or actionable answers → a sandboxed widget only for calculations or games. The catalog generates the model's prompt; specs are schema-validated. Generative cards: one job, 400–600 px wide, purpose visible in the first 300 px, 5–7 options at most, carousel metadata of 3 lines or fewer, stable ids, heavy components deferred until their arguments are complete [github/ai-ui/assistant-ui-assistant-ui; github/ai-ui/openai-apps-sdk-ui; github/ai-ui/vercel-labs-json-render]
- **Third-party UI (MCP Apps, partner HTML)**
  - Build it with: Only in a sandboxed iframe with the restrictive default CSP, logged postMessage traffic, a visible "From {server}" boundary, and the host theme passed as CSS variables. Tool calls the view starts go through the approval ladder [github/ai-ui/modelcontextprotocol-ext-apps]
  - Never: Inline third-party markup
- **Artifacts (long output)**
  - Build it with: A versioned side panel opened from its inline preview. Agent writes are versions; user edits are flagged as manual; versions can be diffed [github/ai-ui/vercel-chatbot]
  - Never: Long output inline in the thread
- **Clarifying questions**
  - Build it with: A sticky `Questionnaire` card above the composer: progress, choices plus "Type another answer…", Previous / Next / Answer. "Preparing a question…" shimmers while the input streams; afterwards a trace line reads "Asked N questions" [github/ai-ui/shadcn-ui-chatbot-template]
  - Never: Numbered questions in prose
- **Agent edits to structured data**
  - Build it with: Land as **pending**, with an AI marker plus an accept / undo pair. After a human edit the marker becomes "Revert to agent value". The AI marker is a toggletip with an explainability popover (overview → details → sources → actions), focusable even in read-only controls, and never triggers actions [articles/ai-ux/salesforce-slds-agentic-patterns; articles/ai-ux/carbon-for-ai]
  - Never: Silently overwritten values
- **Answers**
  - Build it with: Truncated pyramid: the answer and its necessary caveats first, follow-up chips after. "Can't do that" comes first, and "More detail" expands in place. Offer scrutiny follow-ups ("What could make this wrong?") and select-to-ask on any span. Clarifying questions render as a generated form (chips, one question per step), never numbered prose questions [articles/ai-ux/nngroup-ai-ux-research; articles/ai-ux/salesforce-slds-agentic-patterns]
- **Regenerate and branch**
  - Build it with: Regenerating never destroys output: versions cycle ("2 / 3"). "Branch from here" shows the inherited context, with items that can be unticked [articles/ai-ux/shapeof-ai-pattern-library]
  - Never: Overwriting the previous answer
- **Feedback**
  - Build it with: Thumbs up and down together, tertiary placement, a "Thanks" confirmation. Detailed options are named by consequence. Act on feedback immediately [articles/ai-ux/salesforce-slds-agentic-patterns; articles/ai-ux/apple-hig-generative-ai]
- **Composer while running**
  - Build it with: **Stop always visible beside a working Send**: messages sent mid-run queue as steering for the agent. Stop calls a **server stop endpoint** that saves the partial answer and cancels the work (with resumable streams, `stop()` only disconnects). A stopped turn keeps its partial text with a "Stopped by you" badge and Continue / Discard. An optional **Answer now** on the thinking line skips remaining reasoning without stopping the run [youtube/fmZWvE7yDZo; youtube/YNJvm7t3yq8; youtube/RGiXcVxSD3s; github/ai-ui/vercel-ai; github/ai-ui/assistant-ui-assistant-ui; github/ai-ui/ibelick-prompt-kit]
  - Never: A run you can't interrupt or steer
- **Idle composer**
  - Build it with: Capability chips for tasks the agent does reliably, role templates, and a "/ for skills" hint. After an answer: action buttons that carry the output into the next task or integration. Keep deterministic controls for exact operations [youtube/fmZWvE7yDZo; youtube/L3RuP_q8Bwc]
- **Agent driving a surface**
  - Build it with: A persistent border or banner around the controlled browser, canvas or document, with Stop, Ask before acting, and Notify me [youtube/L3RuP_q8Bwc]
- **Memory**
  - Build it with: An inspector showing what's remembered, with delete. A "Saved to memory" chip appears in the turn, with Manage / Undo. Temporary mode shows a persistent "not saved" indicator [youtube/L3RuP_q8Bwc; articles/ai-ux/shapeof-ai-pattern-library]
  - Never: Silent memory

**Approvals** [youtube/CDqzWpwkSls; youtube/fmZWvE7yDZo; youtube/WkBPX-oDMnA]:
- **Tier by cost and risk.** Read-only and cheap tools run unprompted. Writes, sends, spending and irreversible actions need approval. Destructive ones get extra friction. Auto-approved calls render as a status line giving the policy reason.
- **Answers:** Approve · Reject (with a reason that reaches the model) · Edit arguments (only if the schema allows) · Respond instead. Scoped options (allow once / always, reject once / always) show what they grant before commit. [github/ai-ui/langchain-ai-langgraphjs; github/ai-ui/ag-ui-protocol-ag-ui; github/ai-ui/assistant-ui-assistant-ui]
- **Lifecycle:**
  - Cancelled and expired are distinct from Deny.
  - Decide whether a new message blocks or cancels a pending approval.
  - Wait for the server to accept before disabling the buttons.
  - Restore pending approvals from thread state after a reload.
  - Several pending approvals get one card each and one combined submit.
  - Approvals are verified on the server (signed or issued); free text never authorizes. [github/ai-ui/ag-ui-protocol-ag-ui; github/ai-ui/assistant-ui-assistant-ui; github/ai-ui/vercel-ai]
- **Frame the request as a proposal and say what to check:** target, effect, reversibility, evidence. Duolingo moved correct rejections of bad AI flags from 50% to 71% by rewording alone. A bare Approve / Deny on a high-stakes action invites rubber-stamping.
- **One decision per approval.** "Is the agent's reading right?" and "should it act?" are separate questions.
- **Multi-step work:**
  - Approve a numbered plan card first, with the one open question that changes the approach.
  - Then gate step by step.
  - Never "Approve all" on a large diff, and never a confirm on every edit.
- **Approved then edited is a hidden rejection.** Record what the user does after approving (edits, overrides, retries) as distinct events.

**Trace and wait states** [youtube/fmZWvE7yDZo; youtube/maTp79FD9gI; youtube/WkBPX-oDMnA]:
- Completed lines show elapsed time, plus tokens or cost where users pay for them. Retries say "attempt n". A verifier's verdict is a line before the result.
- Use the shimmer only for waits that warrant it; short tool calls stay plain lines. Long runs announce "Working…" to screen readers about every 5 s via a polite live region, stopping at completion; errors are announced. [articles/ai-ux/primer-copilot-accessibility-practices]
- **Wait ladder:** nothing under 1 s; spinners and skeletons appear only after a 300–1000 ms delay; indeterminate for 1–3 s; determinate for 3–10 s; beyond 10 s it becomes a background task that notifies on completion. One spinner per region. First feedback within 100 ms of submit or tool start. On-device models add a "model not ready" stage: determinate download → indeterminate "Loading model" → ready, saying whether the feature works meanwhile. [articles/component-gallery/spinner; articles/clig; github/ai-ui/GoogleChromeLabs-web-ai-demos]
- **Trace logs collapse on success and expand automatically on failure.** [articles/clig]
- **Show what the agent removed, in place:** tinted and struck through, or a collapsed "N deleted" row; never only the end state.
- **Every automatic write announces itself with an Undo** for that action. When users keep overriding a behavior, stop and offer to turn it off. [articles/microsoft-hax G9, G13]
- **Stop responds instantly** and cleans up within a timeout. A second press force-stops, and the UI says so. [articles/clig] **A dropped connection is not a stop:** show "Reconnecting…" and resume the same message. Stop is an explicit signal that works from every tab or device in the session. [youtube/YNJvm7t3yq8]
- **End of run:** a state-changing run says what changed and suggests the next action. A failed or stopped run hands off what was done, what's left, and the manual path. [articles/clig; articles/google-pair; articles/microsoft-hax G10]
- **Confidence** is shown as High / Med / Low or ranked alternatives, each with an action, never a raw percentage. Clarifying questions come in one round, as a ranked choice, only when confidence is in the middle band. [articles/google-pair; articles/microsoft-hax G10-A, G11]
- **Agent output that varies lives in its own region;** controls people use by habit never move. [articles/google-pair]
- **Audit log** of agent actions: actor (with agent badge), event, what changed, status, Undo with a stated window ("Undo for 15 min"), date filter, export. Autonomous actions carry "Why: you allowed X". [articles/checklist-design; articles/ai-ux/smashing-agentic-ux-patterns]
- **Agent-caused errors:** acknowledge → what was corrected → next step → how to reach a human. [articles/ai-ux/smashing-agentic-ux-patterns]
- **First run:** the agent acts on the user's own data (or a sample) rather than coach marks, and offers example actions for common tasks. [articles/ai-ux/lukew-durable-ai-patterns]
- **Mark changes where they happen:** highlighted revisions, a jump-to-next-change control, per-change Keep / Undo plus Accept all, and one-click revert in place for proactive edits. [youtube/L3RuP_q8Bwc; youtube/2cEGQEllBGc]
- **Agent limits end in a human next step** that names who or what can fix it. Agent initiative ("I also noticed…") is labelled apart from the requested work. When the agent is about to make an assumption, it pauses, asks in the same task, and resumes without restarting the run. [youtube/CiMVKnX-CNI; youtube/RGiXcVxSD3s]
- Run summaries go in teaching order: background → the goal in plain words → details, with prose before each change.
- **Panels persist.** Hide and show the sidebar, trace inspector, tool-output drawer and settings with `<Activity mode={open ? "visible" : "hidden"}>`, not `{open && …}`, so search text, scroll and expansion survive. Pre-render the likely next view hidden (the next conversation, an approval's detail) so it opens instantly. [youtube/G9xD6lHgrMM]

**Delegated and background work** [youtube/RGiXcVxSD3s; youtube/YIVkERhy8xo]:
- A **task list** with status per task (awaiting input / running / done / failed), an openable trace per task, and a notification when work is done or needs input. Agent-produced values link to their provenance (source + step).
- An **attention queue**: filter chips All / Awaiting / Working / Idle with counts; rows show the task plus the live last action or "Idle 29m"; one shortcut jumps to the next item awaiting the user.
- **Review packages** for finished work: changed files plus a visual before/after, side-by-side comparison of parallel attempts, and terminal states (Merged / Cancelled).
- **Take-over is always possible:** the user can reclaim any task, and a failing agent backs off and returns control.

**AI inside non-chat surfaces** [youtube/CiMVKnX-CNI; youtube/2cEGQEllBGc]:
- Choose the surface per capability:
  - **Invisible:** pre-work.
  - **Ambient:** small markers on the affected field or row.
  - **Inline:** invoke on the selection; dataset-wide changes run as generated code over the data.
  - **Conversational:** only for building or exploring.
- Proactive help is a *specific* question or proposed change at the object, and is revertible in one click. Never a generic "Ask AI".

**Approval ladder** (refines the tiers above) [articles/clig; articles/microsoft-hax G16]:
1. Read-only → runs with no prompt.
2. Moderate → an inline confirm with a dry-run preview of the effect.
3. Severe or irreversible → a blocking dialog with type-to-confirm (the resource name). *Indirect* destruction, such as a config change that deletes nine things, counts as severe. Initial focus goes to the least destructive button.

"Always allow" states its scope before the user commits: this session / this workspace / always; the exact command vs. every command of that kind; read vs. write or send. A grant history allows revoking. Autonomy is a user-adjustable ladder that starts low, with four named rungs set per tool category: **Suggest / Propose / Act with confirmation / Act and notify**. When approvals are switched off, a persistent "approvals off" indicator offers one-click re-enable. Approval timeouts warn at least 20 s before expiry and can be extended (WCAG 2.2.1). [youtube/L3RuP_q8Bwc; articles/ai-ux/smashing-agentic-ux-patterns]

- **The approval unit is an action card with a lifecycle:** title, one-line effect, Reject / Accept → "Generating preview" → accepted. Collapsed, the line keeps "Accepted by ‹name›" and a rollback note; a failure turns red with Try again. The same component works in chat and inline. Pending or dismissed never mutates data. [youtube/CiMVKnX-CNI; youtube/RGiXcVxSD3s]
- **Plan cards show estimated duration and cost** (money, tokens, credits) and their scope ("only these sites; I'll ask before anything else"). Steps that hand back say so ("I will stop before checkout"). They have three exits: **Proceed · Edit plan · I'll do it myself**. Use domain verbs, never function names. If execution diverges from the approved plan, flag it on the card. [youtube/L3RuP_q8Bwc; articles/ai-ux/smashing-agentic-ux-patterns]
- **Thresholds come from outcome costs, not a confidence number:** price a wrong action against asking or refusing, in user recovery time. Costly or irreversible actions confirm even at high confidence. Make confirming cheap with pre-filled choices. [youtube/Zd5b40Jbp_k]

**Identity and safety** [articles/agent-ui-written-guides]:
- **Agent identity:**
  - Every agent-authored artifact carries an agent badge.
  - The responsible human is shown on delegated work.
  - The four states (thinking / waiting for input / executing / done) are readable at a glance.
  - An invocation is acknowledged immediately.
- **Model output is untrusted user content:**
  - Sanitize the *accumulated* stream (DOMPurify), not individual chunks.
  - If the sanitizer removes anything, stop rendering.
  - Append nodes instead of rewriting `innerHTML` / `textContent` on every chunk.

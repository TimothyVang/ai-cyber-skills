## 1. Workflow: job → plan → diverge → build → motion pass → verify live → critique

1. **Start with the job.** Name who acts, what they're trying to do, the object, and what the system will change. List the reachable states before drawing pixels. [vercel-agents-design-guidance]
2. **Write a token plan before any code** [anthropic frontend-design skill]:
   - Color: OKLCH seeds (brand, neutral tint, each status) on one shared lightness scale, named by role (`bg-subtle`, `fg-muted`, `border-strong`), not by hue. Hex is only an sRGB fallback; see §6a. [youtube/_batch-visual-design]
   - Type: typefaces and the role of each.
   - Layout: a one-line concept plus an ASCII wireframe, including alignment.
   - Principles: what makes this UI specific.
3. **Check the plan against the brief.** For any part you would produce for *any* similar page, revise it and say what changed. [anthropic frontend-design skill]
4. **Answer the direction questions, feed references, then diverge.** Before generating, answer: emotional territory, what it must never feel like, references, audience [youtube/v42opQpCy60]. LLMs regress to the mean, so supply visual references or extracted tokens [youtube/AApjEHsMkTU]. For new surfaces, build 2–4 genuinely different, working directions behind a live picker before committing; they must differ on a named axis, not just accent color [.claude/skills/prototype; youtube/r2P1v64pM28].
   For agent features, prototype the agent's *behavior* in working code (sliders for tone, proactiveness, caution and concision on the real system prompt) before polishing visuals [youtube/CiMVKnX-CNI].
5. **Build with real content.** Real copy and real data shapes; placeholder copy makes a design feel templated. [anthropic frontend-design skill]
6. **Separate the passes:** build, then a dedicated motion pass (`animate`), then critique and polish. [youtube/Ysr7oNDajJI]
7. **Verify the rendered surface** in a browser, in two tiers [youtube/xOO8Wt_i72s]:
   - **After every UI change:** open each changed view, check it against the brief, take a 1440 px screenshot, read the console.
   - **Before a PR or a large refactor:** a phased review:
     - the live flow and every reachable state at 1440 / 768 / 375 px;
     - keyboard, focus, labels and contrast;
     - overflow and loading / empty / error;
     - the console.
   - Also check on a phone or at throttled frame rates.
   - Prefer the browser tool's accessibility snapshot to coordinate clicking; a poor snapshot is itself a finding.
   - Never claim visual quality from reading code. [vercel; anthropic harness; youtube/r2P1v64pM28]
   - **Agent UI is verified against scripted streams first:** `@shadcn/helpers/ai-sdk` `createChat()` replays approve, deny, error, preliminary, long-output and stopped states through the real `useChat`, with no model or network. Only then try a real model. [github/ai-ui/shadcn-ui-chatbot-template]
8. **Critique with a separate pass** that is told to be skeptical, scoring the §2 rubric. Self-grading skews positive. Motion reviews end in an explicit **Block** or **Approve**. [anthropic harness; .claude/skills/review-animations] Rendered video is critiqued with timestamped notes instead of scores (§5a).

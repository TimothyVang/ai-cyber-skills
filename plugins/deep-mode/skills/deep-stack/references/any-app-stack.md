# Build a stack for any app

Use this when the team needs a tech stack for something that is not a plain web or SaaS app, or when the user asks to "build the stack" for any project. It applies the decision rules in `references/philosophy.md` to the app in front of you. The concrete web defaults live in `references/stack.md`.

Be honest about the source of every pick:
- **Default pick:** the source material named this tool for this job. Cite it from `stack.md` or `philosophy.md`.
- **Inferred:** the sources never covered this job. You chose it by applying the rules. Say so, and prove it with research and a prototype before anyone builds on it.

Never present an inferred pick as a default pick.

## Steps

1. **Frame the app.** Write down, in one short block:
   - What it is and who uses it. Type: web/SaaS, API service, CLI, desktop, mobile, AI agent, data or ML pipeline, security tooling, infrastructure, game, embedded.
   - Where it runs: cloud, on-prem, air-gapped, user machines, edge devices.
   - Data it touches and how sensitive it is.
   - Expected scale and the team's skills.
   - Existing code. An existing project's stack wins over every default here.
2. **List hard constraints first.** Compliance and accreditation, network limits (no internet, no SaaS), mandated languages or platforms, licensing, cost ceilings. A hard constraint beats any pick. When it rules out the managed-service defaults, apply the "highest abstraction you're allowed to use" rule instead (see `philosophy.md`) and record why.
3. **Map the layers this app actually needs.** Pick from: interface (web, CLI, TUI, desktop, mobile), core language and runtime, backend or service layer, data storage, background and durable work, AI and agents (models, SDK, tools, sandboxes), auth, payments, integrations, observability, testing and verification, packaging and deploy, repo layout. Drop the layers it doesn't need. A CLI has no auth or payments layer.
4. **Choose each layer.**
   - The default catalog covers this layer and the constraints allow it → use the default pick and cite it.
   - Otherwise → name 2 or 3 candidates and score each against `philosophy.md`. The core checks are: agents know it well and it's configured as code (P16); it's typed end to end (P17); it's the highest abstraction the constraints allow (P3, P4); errors are handled explicitly (P35); no client-to-data shortcuts (P30); it's stable, not beta (P8, P9); cost is accepted where it buys speed or reliability (P48, P50). Cite the rule IDs that decided it.
   - Check each candidate's current docs and release state. Use `npx opensrc <package>` or the official repo so the agent reads real source, not memory.
   - Pick one, label it **inferred**, and write the one-line reason in terms of the rules.
5. **Prototype the riskiest picks.** Take the one or two choices most likely to be wrong (an inferred core runtime, a new storage engine, an agent framework). Run deep-mode's Prototype playbook (`skill://deep-mode/references/playbooks/prototype.md`), or a ten-minute spike. Prove the pick does the app's hardest job. A failed spike means pick the next candidate and say so.
6. **Lay out the repo.** Default to one monorepo, so agents see everything and clients share one core. Name the folders: apps, services, shared packages. Put the service-layer split in it: entry points own the product rules, services own reusable operations (`references/structure.md`).
7. **Write `STACK.md`** at the repo root (merge into an existing one; never overwrite it):

   ```markdown
   # Stack

   **App:** <one line>. **Runs on:** <where>. **Constraints:** <list>.

   | Layer | Pick | Source | Why (rule) | Rejected | Revisit when |
   |---|---|---|---|---|---|
   | Core language | ... | default pick (stack.md §4) or inferred | ... | ... | ... |

   ## Repo layout
   ## Prototype evidence
   ## Open questions
   ```

   Every row names its source and its rule. Every inferred row links its prototype evidence or says "unproven".
8. **Scaffold only when asked.** "Build the stack for me" means create the folders, install the picks, and get a hello-world running through every layer. Without that ask, stop at `STACK.md`. Commit and push per deep-mode's Autonomy section.

## Done when

- Every layer the app needs has one pick with its source and reason.
- Every inferred pick has prototype evidence or is marked unproven.
- `STACK.md` exists and the user saw it.

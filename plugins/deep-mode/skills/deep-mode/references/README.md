# Reference library

Read when a task touches one of these areas and you need to know which reference file to open. Each entry names the files and when to read them. Read only the file the task touches, before designing or reviewing in that area. SKILL.md's gates and playbooks still govern.

**Stack and UI design** come from `skill://deep-stack` (stack picks and the decision rules behind them); its "With deep-mode" section sets the split. Greenfield web, SaaS, or AI-app framework, backend, auth, payments, or deploy choice → its `references/stack.md`. Any other kind of app (CLI, desktop, mobile, agent, data/ML, security tooling), or "build the stack for me" → its `references/any-app-stack.md`, which writes a cited `STACK.md`. Designing a UI with an agent → its `references/design-workflow.md`; rebuilding to the standard of a named reference app → the Reference rebuild playbook. Recording UI proof with no `verify-<app>` skill → its `references/prove.md`. Your gates and playbooks still govern.

**Harnesses, protocols, and AI-native tooling** (using, configuring, or scripting omp, Claude Code, or Codex; MCP, ACP, A2A, WebMCP; skills, plugins, `AGENTS.md`, hooks, sandboxes, headless runs) → read `references/harnesses/README.md`, then only the file the task touches. Those files carry the cited, dated facts (paths, flags, tool names) and the traps for deep-mode in each harness.

**Credentials and agent authentication** (sharing secrets and `.env` safely, password managers, logins and MFA for agents, credential brokers, protecting MCP servers and agent APIs, OAuth delegation, CI OIDC, secret scanning, leak response) → `references/credentials/README.md`. It holds the free-first picks, the rules, and the cited research, checked 2026-11-11.

**Architecture: monorepos, ontology, databases, backend infrastructure** (repo layout and workspace tooling, domain vocabulary and typed models, knowledge graphs and semantic layers, choosing, organizing, or migrating a database, multi-tenancy, queues and durable workflows, API style, reliability, observability, deployment, IaC) → `references/architecture/README.md`, then only the file it routes to. Cited and dated 2026-11-11; it builds on `references/domain-rules/backend-system-design.md` and the model-the-domain principle rather than repeating them.

**Agent tooling** (browser automation, agent sandboxes, coding-agent harnesses or multi-agent orchestrators, autoresearch loops) → read the cited landscape in `research/README.md` of a local checkout of `TimothyVang/automation-tools` before picking a tool. No checkout: `gh repo clone TimothyVang/automation-tools .scratch/refs/automation-tools` from the project root (private; skip if you can't access it). It is a 2026-11-11 snapshot tuned for omp + Orca on Windows, so recheck release dates and licenses of the tool you pick.

**Engineering domain rules** come from `references/domain-rules/` (its `README.md` lists sources). Read only the file the task touches, before designing or reviewing in that area:

- AI agent, agent harness, multi-agent system, MCP or WebMCP, or an agent instruction file (CLAUDE.md, AGENTS.md, a skill) → `references/domain-rules/agent-engineering.md`. Audit agents against all seven of its laws.
- LLM fundamentals, RAG or retrieval, fine-tuning, inference cost or hardware, local models, or model choice → `references/domain-rules/ai-concepts.md`.
- AWS, VPC, cloud connectivity failure, IAM, or cloud cost → `references/domain-rules/aws-networking.md`. A "can't connect" bug starts with its four-step packet check and flow-log table.
- Backend code, API, database, cache, queue, scaling, resilience, observability, security, or language choice → `references/domain-rules/backend-system-design.md`; a specific language's runtime, tooling, or traps → `references/domain-rules/language-ecosystems.md`.
- Linux, shell tools, git, containers, Kubernetes, Terraform, CI/CD, deploy strategy, secrets, or a bug rooted in data structures, complexity, memory, floats, concurrency, or network protocols → `references/domain-rules/devops-and-fundamentals.md`.
- Unfamiliar codebase, stuck on an error, slowness, memory, or race debugging, legacy code, PR or commit text, production incident, estimates, or pushing back on scope → `references/domain-rules/engineering-practice.md`.

**Frontend UI/UX** (building, restyling, or reviewing UI; components; motion and animation; motion graphics or rendered video; color; accessibility; chat or agent UI) → before writing UI code, read `references/frontend/README.md` (always-apply rules, routing, section index), then the `references/frontend/playbook/` section it routes to. `references/frontend/patterns/` holds what the reference images and clips taught, as text: shipped-app layouts, popular pins, 193 animation techniques, the motion-graphics stack. These files are bundled, so they work anywhere deep-mode is installed.

Frontend evidence and media live in the private `TimothyVang/frontend`. When you need them, shallow-clone it to `.scratch/refs/frontend` (SKILL.md Contain the work) and never commit from it.

**Cloud security and DevSecOps rules** come from `references/cloud-devsecops/` (cited reports in `TimothyVang/cloud-devsecops`; its `README.md` lists them). They cover securing and wiring up a cloud, where `domain-rules/aws-networking.md` covers how AWS networking works. Read the file the task touches before designing, reviewing, or changing cloud access, policy, or pipelines:

- AWS accounts, Organizations, SCP/RCP, IAM, GuardDuty or Security Hub, KMS, or CI access to AWS → `references/cloud-devsecops/aws.md`.
- Azure subscriptions, management groups, Entra ID, RBAC, Azure Policy, Defender for Cloud, Key Vault, Private Endpoints, AKS, or CI access to Azure → `references/cloud-devsecops/azure.md`.
- Google Cloud orgs or projects, IAM or service accounts, org policy, VPC Service Controls, Security Command Center, Binary Authorization, GKE, or CI access to GCP → `references/cloud-devsecops/gcp.md`.
- A CI/CD pipeline's security stages, supply chain (SBOM, signing, SLSA provenance), scanners, policy as code, container or Kubernetes hardening, or GitHub Actions hardening → `references/cloud-devsecops/devsecops-pipeline.md`.
- Testing cloud or IaC code without a real account (Floci, LocalStack, moto, Azurite, Google emulators) → `references/cloud-devsecops/local-emulators.md`. Run infra changes there first when the emulator covers the service.
- Choosing terminal, container, Kubernetes, Terraform, or code-review tooling → `references/cloud-devsecops/devops-tools.md`.

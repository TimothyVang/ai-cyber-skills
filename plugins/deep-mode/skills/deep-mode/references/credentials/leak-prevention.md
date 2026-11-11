# Keeping agents from leaking or exfiltrating credentials: free tools, controls, incidents (as of 2026-11-11)

**Summary.** Layer three free controls: (1) a secret scanner at commit and in CI (gitleaks MIT, or TruffleHog AGPL for verified hits) plus GitHub push protection, which is free for public repos only; (2) agent-side read and env scrubbing (Claude Code `Read(...)` deny rules + `sandbox.credentials` + `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`; Codex `shell_environment_policy` with `ignore_default_excludes = false`); (3) default-deny egress (Claude/Codex sandboxes, devcontainer firewall, E2B/Daytona network lists).
Assume prompt injection will happen: 2025-2026 incidents (GitHub MCP, Supabase MCP, s1ngularity, Shai-Hulud, Miasma, Deadbugz) all turned an agent's own reach into the exfil path.
When a secret leaks, revoke it before anything else. Rewriting history does not reach forks, other clones, or cached views. Short-lived OIDC credentials limit how much a leak can do.

Legend: `[unverified]` = not confirmed in a primary source; `[inference]` = my deduction. Release dates come from the GitHub API, checked 2026-11-11.

## 1. Secret scanners

| Tool | What it does | Free terms / license | Latest release | Agent-relevant notes | Source |
|---|---|---|---|---|---|
| gitleaks | Regex+entropy scan of git history, dirs, stdin | MIT, fully free CLI | v8.30.1, 2026-03-21 (commits to 2026-10) | Official pre-commit hook runs `gitleaks git --pre-commit --redact --staged --verbose`; `--redact` keeps secrets out of agent-visible logs | [repo](https://github.com/gitleaks/gitleaks), [hooks](https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml) |
| gitleaks-action | GitHub Action wrapper | Free license key required for org-owned repos, not personal; GitHub reports license NOASSERTION (not a standard OSS license) | v3.0.0, 2026-05-30 (Node 24) | v2 stops working after Node 20 removal on 2026-09-16; use `@v3` | [repo](https://github.com/gitleaks/gitleaks-action) |
| Betterleaks | New scanner from the gitleaks maintainers incl. original author; Aikido-sponsored | MIT | v1.10.0, 2026-11-04 (repo created 2026-02-03) | Validation is opt-in (`-v`), optional revocation; scans GitHub/GitLab issues, PRs, HF, S3, containers; `main` is v2 pre-release | [repo](https://github.com/betterleaks/betterleaks) |
| TruffleHog OSS | 800+ detectors, live verification against provider APIs | AGPL-3.0 (copyleft; fine to run, obligations if you modify and offer as a service) | v3.99.8, 2026-11-02 | `--results=verified` cuts noise; hook: `trufflehog git file://. --since-commit HEAD --results=verified --fail`; verification makes outbound calls with the found secret [inference] | [repo](https://github.com/trufflesecurity/trufflehog), [hooks](https://github.com/trufflesecurity/trufflehog/blob/main/.pre-commit-hooks.yaml) |
| ggshield (GitGuardian) | CLI and hooks backed by GitGuardian SaaS | Client MIT; Starter plan free: up to 25 devs, unlimited real-time scanning, up to 500 historical scan detections, 10K API calls/month | v1.56.1, 2026-10-26 | Needs a GitGuardian API key, so content is scanned by their API [inference]; not offline | [repo](https://github.com/GitGuardian/ggshield), [pricing](https://www.gitguardian.com/pricing) |
| detect-secrets (Yelp) | Baseline-file workflow, plugin detectors | Apache-2.0 | v1.5.0, 2024-05-06 | **Stale:** no release in 30 months (last push 2026-04); prefer gitleaks/Betterleaks for new setups | [repo](https://github.com/Yelp/detect-secrets) |
| pre-commit | Hook runner for the above | MIT | v4.7.0, 2026-10-13 | Client hooks are bypassable (`SKIP=gitleaks`, `--no-verify`), so pair with server-side checks | [repo](https://github.com/pre-commit/pre-commit), [gitleaks README](https://github.com/gitleaks/gitleaks) |
| GitHub secret scanning | Scans all branches/history, issues, PRs, discussions, wikis | Free and automatic for public repos; private org repos need GitHub Secret Protection ($19/active committer/month, Team or Enterprise Cloud) | SaaS | Partner program notifies issuers for revocation; free org "secret risk assessment" report | [docs](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning), [plans](https://github.com/security/plans) |
| GitHub push protection | Blocks pushes containing secrets | "Push protection for users" is on by default and free, but only for pushes to public repos; repo-level needs Secret Protection | SaaS | Also covers GitHub MCP server writes (public repos only); anyone with write access can bypass with a reason by default | [docs](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection) |

Rules:
- Run one scanner locally (pre-commit) and the same or a second one in CI on every push/PR. Client hooks are advisory because an agent can pass `--no-verify`.
- Always use `--redact` (gitleaks) in agent sessions so the finding itself does not put the secret into the transcript.
- Commit a `.gitignore` that covers `.env`, `.env.*` (keep `!.env.example`), `*.pem`, `*.key`, and cloud credential files before the agent's first commit.

```yaml
# .pre-commit-config.yaml (run `pre-commit autoupdate` to pin the latest rev)
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks: [{ id: gitleaks }]
```

## 2. Agent-side controls (read, env, hooks, MCP)

| Control | What it does | Free terms / license | Latest release | Agent-relevant notes | Source |
|---|---|---|---|---|---|
| Claude Code `Read(...)` deny rules | Blocks built-in file tools from reading paths | Part of Claude Code (proprietary, no OSS license) | v2.1.322, 2026-11-10 | Also covers recognized Bash file commands (`cat`, `head`, `tail`, `sed`, redirections), but **not** `grep -r .` or scripts that open files themselves; use the sandbox for OS-level blocking | [permissions](https://code.claude.com/docs/en/permissions) |
| Claude Code sandbox | OS sandbox for Bash (Seatbelt on macOS, bubblewrap on Linux/WSL2) | Built on `sandbox-runtime`, Apache-2.0 | runtime v0.0.82, 2026-11-09 | **Off by default.** Default reads include `~/.ssh` and `~/.aws/credentials`, and env vars (with secrets) are inherited. Not available on native Windows (use WSL2) | [sandboxing](https://code.claude.com/docs/en/sandboxing), [runtime](https://github.com/anthropic-experimental/sandbox-runtime) |
| `sandbox.credentials` deny/mask | Denies credential files, unsets env vars; `mask` gives commands a sentinel and the proxy injects the real value only to `injectHosts` | Built in | 2026 docs | No built-in deny list: only what you list is protected. `mask` needs `network.tlsTerminate` and is honored only from user/managed/CLI settings, not repo settings | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` | Strips credentials from Bash, hooks, stdio MCP server envs | Built in | 2026 docs | Leaves GitHub tokens and proxy settings in place by design | [env vars](https://code.claude.com/docs/en/env-vars) |
| Codex sandbox | OS sandbox; `workspace-write` with network **off** by default | Codex CLI Apache-2.0 | rust-v0.167.1, 2026-11-10 | Enable network only via `[sandbox_workspace_write] network_access = true`, then constrain with `features.network_proxy` domain rules | [security](https://developers.openai.com/codex/agent-approvals-security), [repo](https://github.com/openai/codex) |
| Codex `shell_environment_policy` | Controls env vars passed to spawned commands | Built in | 2026 docs | **`ignore_default_excludes` defaults to `true`, so vars containing KEY/SECRET/TOKEN ARE passed unless you set it to `false`** | [advanced config](https://developers.openai.com/codex/config-file/config-advanced), [reference](https://developers.openai.com/codex/config-reference) |
| Claude Code PreToolUse hooks | Script returns `permissionDecision: "deny"` before a tool runs | Built in | 2026 docs | String matching is defense in depth only; hooks run outside the sandbox with your full access | [hooks](https://code.claude.com/docs/en/hooks) |
| Snyk Agent Scan (ex mcp-scan) | Scans MCP configs, tools, skills for poisoning | Apache-2.0 client; requires Snyk account/API token | v0.6.11, 2026-11-06 | Sends tool names, descriptions, MCP configs to Snyk API (secrets redacted first), so not offline | [repo](https://github.com/invariantlabs-ai/mcp-scan) |

Claude Code baseline (user settings `~/.claude/settings.json`, so a repo cannot weaken it):

```json
{
  "permissions": { "deny": ["Read(.env)", "Read(.env.*)", "Read(!.env.example)", "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(**/*.pem)"] },
  "sandbox": {
    "enabled": true, "allowUnsandboxedCommands": false, "failIfUnavailable": true,
    "filesystem": { "denyRead": ["~/**/.env*", "~/**/*.env", "~/**/*.pem", "~/**/id_rsa", "~/**/id_ed25519", "~/**/.aws/credentials"] },
    "network": { "allowedDomains": ["registry.npmjs.org", "pypi.org", "files.pythonhosted.org"], "strictAllowlist": true },
    "credentials": {
      "files": [{ "path": "~/.ssh", "mode": "deny" }, { "path": "~/.aws/credentials", "mode": "deny" }],
      "envVars": [{ "name": "NPM_TOKEN", "mode": "deny" }, { "name": "GITHUB_TOKEN", "mode": "deny" }]
    }
  }
}
```
Settings keys and the `!` carve-out syntax come from [permissions](https://code.claude.com/docs/en/permissions) and [sandboxing](https://code.claude.com/docs/en/sandboxing). The `!` carve-out reaches only rules in the same settings file. On Windows, paths are normalized to `/c/...` form, and `//**/.env` matches every drive.
`filesystem.denyRead` is what stops shell commands (`grep -r .`, `cat`, scripts) from reading project `.env` and key files, and its globs match the same names as the hook below (`.env*` covers `.env`, `.env.local`, `.env-local`, `.envrc`): the sandbox has no built-in deny list, and `credentials.files` above covers only `~/.ssh` and `~/.aws/credentials`. In user settings a `~/` glob covers projects under your home directory; add the same entries for each other top-level directory that holds projects (`/srv/**/.env*`), because on Linux and WSL2 a wildcard works only after the first directory name ([path prefixes](https://code.claude.com/docs/en/settings-reference)). It also hides `.env.example` from shell commands; the Read tool still reaches it.

Codex baseline (`~/.codex/config.toml`), following [advanced config](https://developers.openai.com/codex/config-file/config-advanced):

```toml
sandbox_mode = "workspace-write"          # network_access stays false by default
[shell_environment_policy]
inherit = "core"
ignore_default_excludes = false            # drop *KEY*, *SECRET*, *TOKEN* vars
[shell_environment_policy.filters]
"AWS_*" = "exclude"
"AZURE_*" = "exclude"
"GOOGLE_*" = "exclude"
```

Hook that blocks secret-file access (`.claude/hooks/deny-secrets.sh`, registered under `PreToolUse` with matcher `Read|Grep|Glob|Bash`; output shape from [hooks](https://code.claude.com/docs/en/hooks)):

```bash
#!/usr/bin/env bash
in=$(cat)
deny() { jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'; exit 0; }
hit=$(jq -r '.tool_input | tostring' <<<"$in" | grep -Eio '(\.env[^"/\\[:space:]]*|id_rsa|id_ed25519|\.pem|\.aws/credentials)' | grep -Eiv '^\.env\.(example|sample|template)$' | head -n1)
[ -n "$hit" ] && deny "secret path blocked: $hit"
# Grep over a directory reads every file below it, so check what it would reach. `type` and `glob` are not trusted:
# `type: json` with a hidden-file glob still reaches .env.production.json.
if [ "$(jq -r .tool_name <<<"$in")" = Grep ]; then
  dir=$(jq -r '.tool_input.path // .cwd' <<<"$in"); case "$dir" in /*|[A-Za-z]:*) ;; *) dir="$(jq -r .cwd <<<"$in")/$dir" ;; esac
  sec=$(find "$dir" \( -name .git -o -name node_modules \) -prune -o -type f -print 2>/dev/null | grep -Ei '/([^/]*\.env|\.env[^/]*|id_rsa|id_ed25519|[^/]*\.pem)$|/\.aws/credentials$' | grep -Eiv '/\.env\.(example|sample|template)$' | head -n1)
  [ -n "$sec" ] && deny "Grep over $dir would read $sec; narrow path to files or dirs without secrets"
fi
exit 0
```
The hook sees only the tool call, so a Bash `grep -r .` or a script that opens files still reaches secrets; the baseline's sandbox `filesystem.denyRead` globs close that path.

MCP rules from the official [security best practices](https://modelcontextprotocol.io/docs/draft/tutorials/security/security_best_practices) (draft-track page) and [spec](https://modelcontextprotocol.io/specification/2025-11-25):
- **Token passthrough is forbidden:** servers MUST NOT accept tokens not issued for them, and forwarding a client token downstream creates a confused deputy and breaks audit trails.
- **Confused deputy:** OAuth proxy servers with a static client ID MUST do per-client consent, exact `redirect_uri` matching, and single-use `state`.
- **Local server compromise:** clients MUST show the full startup command before one-click install and SHOULD sandbox servers with minimal filesystem and network access. Local servers should prefer stdio or an authenticated transport.
- **Scope minimization:** start with minimal scopes and step up per operation, because a broad token turns one leak into lateral access.
- **Tool poisoning:** the spec says tool descriptions and annotations are untrusted unless the server is trusted. Invariant Labs showed hidden instructions in a tool description that make the agent read local config and key files and pass them out as a tool argument. They also showed "rug pulls", where a tool description changes after approval ([Invariant, 2025-04-01](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)).

## 3. Documented incidents, 2025-2026

| When | Incident | How credentials or data left | Lesson | Source |
|---|---|---|---|---|
| 2025-05-26 | GitHub MCP "toxic agent flow" | A malicious public issue made an agent with a broad GitHub token copy private-repo data into a public PR | Not fixable server-side; scope tokens per repo and gate cross-repo actions | [Invariant](https://invariantlabs.ai/blog/mcp-github-vulnerability) |
| 2025-07 | Supabase MCP | Instructions in a support ticket made a Cursor agent running with `service_role` (bypasses RLS) copy private table data into a customer-visible reply | Never give agents `service_role`; read-only plus project scoping; review tool calls | [General Analysis](https://generalanalysis.com/blog/supabase-mcp-blog), [Supabase SECURITY.md](https://github.com/supabase/mcp/blob/main/SECURITY.md) |
| 2025-07 | Amazon Q for VS Code v1.84.0 | A poisoned prompt shipped in the extension | Agent prompts and configs are supply chain | [OWASP ASI04](https://genai.owasp.org/download/52117) |
| 2025-08-26 | s1ngularity / Nx | A GitHub Actions injection stole the NPM token. The malicious postinstall hook ran local AI CLIs with `--dangerously-skip-permissions`, `--yolo`, `--trust-all-tools` to hunt secrets, then pushed them to a public `s1ngularity-repository`. Phase 2 made 5,500+ private repos public | Never leave bypass-permission aliases or long-lived tokens on dev machines; use trusted publishing | [Nx postmortem](https://nx.dev/blog/s1ngularity-postmortem), [GHSA](https://github.com/advisories/GHSA-cxm3-wv7p-598c), [Wiz](https://www.wiz.io/blog/s1ngularity-supply-chain-attack) |
| 2025-09 | Shai-Hulud worm | 500+ npm packages; harvested GitHub PATs and AWS/GCP/Azure keys, then self-propagated | Rotate npm/GitHub tokens; enforce phishing-resistant MFA | [CISA](https://www.cisa.gov/news-events/alerts/2025/09/23/widespread-supply-chain-compromise-impacting-npm-ecosystem) |
| 2025-11-24 | Shai-Hulud 2.0 | A preinstall script ran TruffleHog to harvest creds and pushed them to new public GitHub repos | PostHog moved to trusted publishing and pnpm 10 (lifecycle scripts off, `minimumReleaseAge`) | [PostHog](https://posthog.com/blog/nov-24-shai-hulud-attack-post-mortem) |
| 2026-05/06 | Mini Shai-Hulud and Miasma | A stale OIDC trust in TanStack CI led to a planted Claude Code hook that survived uninstall. Miasma committed `.claude/settings.json` SessionStart hooks, `.gemini/settings.json`, `.cursor/rules/setup.mdc`, and a `.vscode/tasks.json` `folderOpen` task that harvest creds when the repo is opened | Treat agent config dirs as executable code in review | [OWASP Q3 2026](https://genai.owasp.org/2026/10/08/genai-and-agentic-ai-exploit-roundup-q3-2026/), [StepSecurity](https://www.stepsecurity.io/blog/miasma-worm-hits-microsoft-again-azure-functions-action-and-72-other-repositories-disabled-after-supply-chain-attack-targeting-ai-coding-agents) |
| 2026-08-10 | Deadbugz malicious MCP | A server behaved normally for 3 calls, then rewrote its tool metadata to steer agents to SSH keys, AWS creds, shell history, kubeconfig | Pin and re-approve tool definitions; deny credential reads by default | [Pillar](https://www.pillar.security/blog/deadbugz-currently-active-mcp-supply-chain-campaign), [OWASP Q3 2026](https://genai.owasp.org/2026/10/08/genai-and-agentic-ai-exploit-roundup-q3-2026/) |
| 2026-07 | Evaluation agents escaping scope | OWASP's roundup reports OpenAI evaluation agents reaching Hugging Face via exposed credentials | Exposed creds turn agent mistakes into intrusions | [OWASP Q3 2026](https://genai.owasp.org/2026/10/08/genai-and-agentic-ai-exploit-roundup-q3-2026/) |

## 4. OWASP framing

- **LLM Top 10 2025:** LLM02 Sensitive Information Disclosure, LLM06 Excessive Agency, LLM01 Prompt Injection, LLM03 Supply Chain ([list](https://genai.owasp.org/llm-top-10/)). A **2026 edition** was released 2026-09-01. It moves Excessive Agency to #3 ([announcement](https://genai.owasp.org/2026/09/01/owasp-genai-security-project-unveils-2026-top-10-for-llm-applications-new-agent-control-standard-and-sponsors-as-community-tops-30000-members/)), and the Q3 roundup cites LLM02:2026 Sensitive Information Disclosure and LLM04:2026 Supply Chain. I could not retrieve the full 2026 list text [unverified].
- **Top 10 for Agentic Applications 2026** (Dec 2025, CC BY-SA 4.0): ASI01 Goal Hijack, ASI02 Tool Misuse (covers tool poisoning), ASI03 Identity and Privilege Abuse, ASI04 Agentic Supply Chain, ASI05 Unexpected Code Execution, ASI06 Memory and Context Poisoning, ASI07 Insecure Inter-Agent Communication, ASI08 Cascading Failures, ASI09 Human-Agent Trust Exploitation, ASI10 Rogue Agents ([PDF](https://genai.owasp.org/download/52117)).
- ASI03 mitigations relevant here: task-scoped, time-bound tokens per agent; just-in-time ephemeral credentials bound to a session; do not let agents cache credentials across tasks. The document's overall principle is "Least-Agency" ([PDF](https://genai.owasp.org/download/52117)).

## 5. Egress control and sandboxing

| Option | What it does | Free terms / license | Latest release | Agent-relevant notes | Source |
|---|---|---|---|---|---|
| Claude Code sandbox network | Proxy allowlist, starts empty; no direct route out | Free with Claude Code | 2026 docs | Hostname-only filtering with no TLS inspection, so broad entries like `github.com` are exfil paths (domain fronting). WebFetch, MCP servers, and hooks are outside the sandbox | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| Claude Code reference devcontainer | Container plus `init-firewall.sh` egress allowlist | Example config in the Claude Code repo | 2026 docs | Even with the firewall, `--dangerously-skip-permissions` lets a malicious repo exfiltrate anything in the container, including `~/.claude` creds; do not mount `~/.ssh` | [devcontainer](https://code.claude.com/docs/en/devcontainer), [script](https://github.com/anthropics/claude-code/blob/main/.devcontainer/init-firewall.sh) |
| devcontainers CLI | Run any devcontainer headless (CI, agents) | MIT | no GitHub releases; last push 2026-11-05 | Pair with a firewall like the one above | [repo](https://github.com/devcontainers/cli) |
| Codex network proxy | Domain allow/deny for sandboxed commands | Apache-2.0 | rust-v0.167.1 | Network on + proxy off = unrestricted; full sandbox escalation bypasses the proxy | [security](https://developers.openai.com/codex/agent-approvals-security) |
| E2B | Firecracker cloud sandboxes via SDK | SDK Apache-2.0; Hobby free: $100 one-time credit, sessions up to 1 h, 10 concurrent | SDK 2.63.0, 2026-11-04 | **Internet on by default**; set `allowInternetAccess: false` or `network.denyOut`/`allowOut`. The egress proxy can fill stored secrets into HTTPS headers outside the sandbox (`Secret.fill`) | [pricing](https://e2b.dev/pricing), [network](https://e2b.dev/docs/sandbox/internet-access), [repo](https://github.com/e2b-dev/E2B) |
| Daytona | Cloud sandboxes | $200 free compute; **OSS repo archived June 2026** (core moved to a private codebase), so treat it as SaaS | last OSS v0.190.0, 2026-06-23 | `networkBlockAll`, `domainAllowList`, `networkAllowList`; Tier 1/2 orgs get restricted egress they cannot override | [pricing](https://www.daytona.io/pricing), [network](https://www.daytona.io/docs/en/network-limits), [repo](https://github.com/daytonaio/daytona) |

Rules:
- Default-deny egress and allowlist package registries plus the one API the task needs. Keep `api.github.com` (write-capable) separate from read-only mirrors when you can [inference].
- Prefer injecting secrets at the proxy (Claude `mask`, E2B `Secret.fill`) so the agent process never holds the value.
- Do not run agents with bypass flags on a host that has real credentials; run them in a container or VM with only task-scoped tokens.

## 6. Response: rotation playbook and history-rewrite limits

1. **Revoke or rotate first.** GitHub says this is step one and often sufficient. GitHub Support helps purge data only when rotation cannot mitigate the risk ([GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)).
2. **Check for use:** provider audit logs; GitHub security log `action:repo.create` for exfil repos; IOCs such as `/tmp/inventory.txt` for s1ngularity ([GHSA](https://github.com/advisories/GHSA-cxm3-wv7p-598c)). Also rotate everything that was in env vars or shell history on the host ([StepSecurity](https://www.stepsecurity.io/blog/miasma-worm-hits-microsoft-again-azure-functions-action-and-72-other-repositories-disabled-after-supply-chain-attack-targeting-ai-coding-agents)).
3. **Hunt persistence:** shell rc files (s1ngularity appended `sudo shutdown -h 0`, per [Nx](https://nx.dev/blog/s1ngularity-postmortem)), `.claude/`, `.gemini/`, `.cursor/rules/`, `.vscode/tasks.json`, `.mcp.json`.
4. **Rewrite only if needed:** `git-filter-repo --sensitive-data-removal --invert-paths --path FILE` (needs v2.47 or later). Limits: commits stay reachable in forks, in other clones, via SHA in cached views, and through PRs until Support dereferences them. Rewriting also drops commit signatures ([GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)).
5. Tool freshness: git-filter-repo's last release is v2.47.0 (2024-12-04, older than 12 months), but commits continue (2026-07) and GitHub reports license NOASSERTION ([repo](https://github.com/newren/git-filter-repo)). BFG is GPL-3.0 with its last release on 2025-01-18 and no commits since, so treat it as **unmaintained** ([repo](https://github.com/rtyley/bfg-repo-cleaner)).
6. **Shrink blast radius next time:** GitHub Actions OIDC replaces long-lived cloud secrets with short-lived tokens ([GitHub](https://docs.github.com/en/actions/concepts/security/openid-connect)). npm trusted publishing removes `NPM_TOKEN` from CI ([npm](https://docs.npmjs.com/trusted-publishers)). Audit OIDC trust policies too, because a stale trust was the Mini Shai-Hulud entry point ([OWASP Q3 2026](https://genai.owasp.org/2026/10/08/genai-and-agentic-ai-exploit-roundup-q3-2026/)).

## 7. Checklist an agent runs before commit or push

```bash
# 1. Nothing secret-shaped is staged
git diff --cached --name-only | grep -Ei '(^|/)\.env($|\.)|\.pem$|\.key$|\.p12$|id_(rsa|ed25519)|credentials' | grep -Eiv '\.env\.(example|sample|template)$' && echo "STOP: secret-like file staged"
# 2. .env is ignored
git check-ignore -q .env || echo "STOP: .env not in .gitignore"
# 3. Scan staged content, redacted output
gitleaks git --pre-commit --redact --staged --verbose
# 4. Before push: scan every commit not yet on the remote
gitleaks git --redact --log-opts="origin/HEAD..HEAD" .
# 5. Optional: verified-only check (makes outbound calls to providers)
trufflehog git file://. --since-commit HEAD --results=verified --fail
# 6. Agent and editor config changes need human review (Miasma vector)
git diff --cached --name-only | grep -E '^\.(claude|gemini|cursor|codex|vscode)/|(^|/)\.mcp\.json$|AGENTS\.md$|CLAUDE\.md$'
```
- Never pass `--no-verify`, `SKIP=gitleaks`, or a push-protection bypass to get past a finding. Stop and report to the human instead.
- Never print, echo, or `cat` a secret to verify it. Check that it is set instead (`[ -n "$VAR" ]`).
- If a scan hits, unstage the file, move the value to the secret store or `.env`, and tell the human to rotate it if it was ever committed or pushed.

## Threats and failure modes

- **Indirect prompt injection drives the agent's own tools:** issues, tickets, web pages, and tool descriptions carry instructions that make the agent read secrets and write them to a public sink ([Invariant GitHub MCP](https://invariantlabs.ai/blog/mcp-github-vulnerability), [General Analysis](https://generalanalysis.com/blog/supabase-mcp-blog), [OWASP ASI01](https://genai.owasp.org/download/52117)).
- **Malware puppeting AI CLIs:** s1ngularity invoked installed agents with bypass flags to hunt for secrets ([Wiz](https://www.wiz.io/blog/s1ngularity-supply-chain-attack)). Any agent CLI on PATH is a capability an attacker can use.
- **Repo-shipped agent config is code:** SessionStart hooks and always-apply rules run when a repo is opened ([StepSecurity](https://www.stepsecurity.io/blog/miasma-worm-hits-microsoft-again-azure-functions-action-and-72-other-repositories-disabled-after-supply-chain-attack-targeting-ai-coding-agents)).
- **Post-approval tool changes:** MCP rug pulls and runtime-gated metadata poisoning ([Invariant](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks), [Pillar](https://www.pillar.security/blog/deadbugz-currently-active-mcp-supply-chain-campaign)).
- **Env inheritance:** Claude's sandbox inherits env vars, and Codex passes `*TOKEN*` vars unless `ignore_default_excludes = false` ([Claude](https://code.claude.com/docs/en/sandboxing), [Codex](https://developers.openai.com/codex/config-file/config-advanced)).
- **Partial coverage:** `Read` deny misses scripts that open files themselves. The sandbox misses file tools, hooks, and MCP servers, and is absent on native Windows ([permissions](https://code.claude.com/docs/en/permissions), [sandboxing](https://code.claude.com/docs/en/sandboxing)).
- **Over-broad allowlists and escape hatches:** `github.com` in an allowlist, unsandboxed retries, `bypassPermissions` mode, `allowUnixSockets` for `docker.sock` ([sandboxing](https://code.claude.com/docs/en/sandboxing)).
- **Over-privileged tokens:** `service_role`, org-wide PATs, and broad MCP scopes turn one injection into full access ([MCP scope minimization](https://modelcontextprotocol.io/docs/draft/tutorials/security/security_best_practices), [OWASP ASI03](https://genai.owasp.org/download/52117)).
- **Scanner-side leaks:** verification and SaaS scanners send candidate secrets off-box ([inference] from [TruffleHog](https://github.com/trufflesecurity/trufflehog) verification and [Snyk Agent Scan](https://github.com/invariantlabs-ai/mcp-scan) data-sharing notes); unredacted findings land in transcripts.
- **False comfort from a history rewrite:** forks, clones, and cached SHAs keep the secret ([GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)).

## Recommendation for a solo dev / small team, all free

1. Add `pre-commit` + gitleaks (MIT) locally, and gitleaks CLI or `gitleaks-action@v3` in CI (the action needs a free key for org repos). Make repos public only if you also want GitHub's free scanning and push protection; private-repo push protection costs $19/committer/month.
2. In user-level Claude Code settings: `Read` deny rules for `.env*`, keys, and cloud creds; `sandbox.enabled` with `allowUnsandboxedCommands: false`, `failIfUnavailable: true`, a strict registry-only allowlist, and `sandbox.credentials` deny entries; export `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`. On Windows, run agents in WSL2 so the sandbox works.
3. In Codex: keep `workspace-write` with network off, and set `shell_environment_policy` with `inherit = "core"` and `ignore_default_excludes = false`.
4. For unattended or `--dangerously-skip-permissions` runs, use the reference devcontainer with `init-firewall.sh`, or E2B Hobby with `allowInternetAccess: false`. Never mount `~/.ssh` or cloud credential files.
5. Give agents task-scoped tokens: fine-grained per-repo GitHub tokens, read-only DB roles (never `service_role`), and OIDC plus npm trusted publishing in CI so long-lived publish tokens do not exist.
6. Review every diff touching `.claude/`, `.gemini/`, `.cursor/`, `.vscode/tasks.json`, or `.mcp.json`. Add MCP servers like dependencies: pin versions, read tool descriptions, and re-approve when they change.
7. On any leak: rotate first, check logs, hunt persistence, then optionally run `git-filter-repo --sensitive-data-removal`.

---
name: secrets-and-auth
description: "Rules and free-first tool picks for secrets and agent authentication: .env and secret sharing, password managers, logins and MFA for agents, OAuth delegation, MCP server auth, CI OIDC, secret scanning, and leak response. Use when a task touches secrets, credentials, tokens, logins, or auth."
metadata:
  as-of: "2026-11-11"
---

# Credentials, secrets, logins, and agent authentication

Read before any task that touches API keys, tokens, `.env` files, passwords, usernames, logins, MFA, OAuth, MCP auth, CI credentials, or a suspected leak. Researched 2026-11-11 against primary sources (vendor docs and pricing pages, GitHub repos and releases, RFCs and IETF drafts, the MCP spec, OWASP). Every claim in the files below carries its link; `[inference]` and `[unverified]` mean what they say. Free tiers and licenses change: recheck the one you pick.

| File | Read when |
|---|---|
| `references/secrets-and-env.md` | Storing, sharing, encrypting, or injecting API keys and `.env` (dotenvx, SOPS + age, Infisical, Bitwarden Secrets Manager, OpenBao, Doppler, Phase); credential brokers; how omp, Claude Code, and Codex pass env and MCP secrets |
| `references/logins-and-passwords.md` | Usernames, passwords, website and CLI logins, TOTP and passkeys (Bitwarden + Agent Access, Vaultwarden, KeePassXC, gopass, Proton Pass); browser session reuse; dedicated agent accounts; passing secrets to commands; transcripts on disk |
| `references/agent-authentication.md` | Protecting an MCP server or agent API, on-behalf-of delegation, human approval, CI and cloud federation (MCP auth 2026-07-28, OAuth 2.1, RFC 8693, DPoP, device flow, CIBA, ID-JAG, SPIFFE); OSS identity servers (Keycloak, Better Auth, Pomerium, Zitadel, authentik); hosted free tiers |
| `references/leak-prevention.md` | Secret scanning, agent read and env controls, egress sandboxes, documented 2025-2026 incidents, rotation playbook, and the pre-commit checklist |

## Rules for the agent

1. **Never print, paste, or commit a secret value.** The agent may read `.env` files when the task needs them; prefer `.env.example` or `.env.schema` for names, check presence with `[ -n "$VAR" ]`, and run commands through an injector (`dotenvx run -- <cmd>`, `sops exec-env <file> '<cmd>'`, `infisical secrets-manager run -- <cmd>`, `bws run -- '<cmd>'`). A value the model sees lands in the session transcript on disk (`~/.claude/projects/`, `~/.codex/sessions/`, `~/.omp/agent/sessions/`) and at the model provider: rotate it if it may have leaked, deleting the message is not enough.
2. **Prefer, in order:** (a) a broker that keeps the real value out of the agent entirely (Claude Code sandbox `mask`, Varlock proxy in a container, Infisical Agent Vault, Bitwarden Agent Access `aac run`, Pomerium or Composio for OAuth tokens); (b) a session or token for the agent's own account; (c) a value read from a vault, only for low-value accounts.
3. **Agents get their own identities.** A machine or bot account, a fine-grained token scoped to the repos or project the task needs, the shortest expiry that works, one identity per agent so you can revoke one. Never a human's personal login, admin token, TOTP seed, or passkey.
4. **Logins without passwords.** A human signs in once; the agent reuses the browser session (Playwright `--storage-state` or a dedicated `--user-data-dir` under `.scratch/auth/`) or the CLI's keychain login (`gh`, `az`, `gcloud`, `aws sso`). Headless logins use the OAuth device flow; the human checks the `user_code`.
5. **Secrets reach commands through stdin, never argv:** `... | docker login --password-stdin`. Arguments show in the process list, shell history, and the transcript of the tool call.
6. **MCP configs hold references, never literals:** `${VAR}` in Claude Code `.mcp.json`, `env_vars` or `bearer_token_env_var` in Codex, `${VAR}` or `"!cmd"` in omp. MCP servers never pass a client's token through to another API.
7. **CI uses OIDC, not stored cloud keys,** with the trust policy pinned to repo and environment (`sub`). npm publishes through trusted publishing.
8. **Scan before every commit and push** (gitleaks with `--redact`; checklist in `leak-prevention.md`). Never bypass a hook, push protection, or scanner finding; stop and tell the user.
9. **Agent config is code.** Review diffs to `.claude/`, `.codex/`, `.gemini/`, `.cursor/`, `.vscode/tasks.json`, `.mcp.json`, `AGENTS.md`, and `CLAUDE.md` like executable changes; pin MCP servers and re-approve them when their tools change.
10. **Changing the user's machine is the user's call.** Creating vault accounts, writing `~/.codex/config.toml` or `~/.claude/settings.json`, storing keys in the OS keychain, and installing tools globally are hard stops (deepmodebot's SKILL.md Autonomy): propose the exact change and let the user apply or approve it.
11. **On a leak:** revoke or rotate first, check provider logs, hunt persistence in agent config folders and shell rc files, then rewrite history only if still needed. Forks and clones keep the old commits.

## What deepmodebot enforces

Nothing on reads. deepmodebot's guard (`skill://deepmodebot/assets/contain/claude_guard.py`, `skill://deepmodebot/assets/contain/omp-contain.ts`) only keeps writes inside the project root; agents can read `.env`, keys, credential files, and saved sessions. The rules above are what keep values out of output and commits. To block reads, apply the optional settings below.

## Optional harness settings (user-level, the user applies them)

| Harness | Setting | Why |
|---|---|---|
| Claude Code | `permissions.deny` for `Read(.env.keys)`, `Read(~/.ssh/**)`, `Read(~/.aws/**)`; `sandbox.enabled` with `allowUnsandboxedCommands: false`, `failIfUnavailable: true`, a strict network allowlist, and `sandbox.credentials` deny or `mask` entries; `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` | Deny rules miss `grep -r` and scripts; only the sandbox blocks at the OS level. The sandbox is off by default, inherits env, and does not run on native Windows (use WSL2) |
| Codex | `[shell_environment_policy] inherit = "core"`, `ignore_default_excludes = false`; keep `workspace-write` with network off | By default Codex passes variables named `*KEY*`, `*SECRET*`, `*TOKEN*` to every command |
| omp | `secrets.enabled: true` in `config.yml`; install `skill://deepmodebot/assets/contain/omp-contain.ts`; `bash.patterns` deny rules if needed | Secret obfuscation is off by default; it swaps secret-looking values for placeholders before provider calls |

## Free stack for a solo dev or small team

| Need | Free pick | Notes |
|---|---|---|
| `.env` in git | dotenvx (BSD-3) or SOPS + age (MPL-2.0, BSD-3) | One age key per person, machine, and CI runner in `.sops.yaml`; `.env.keys` never committed |
| Central secrets | Infisical Free (5 identities) or self-hosted Infisical, Phase, or OpenBao; Bitwarden Secrets Manager Free (2 users, 3 projects, 3 machine accounts) | One machine identity per agent, read-only, one environment |
| Agent never holds the key | Claude Code sandbox `mask`, Varlock proxy in a container, Infisical Agent Vault (5,000 brokered requests a month free) | Real value added at the network edge for allowed hosts only |
| Passwords and usernames | Bitwarden Free with a separate agent account in the free two-person organization, or Vaultwarden (AGPL) self-hosted; KeePassXC with one `.kdbx` per agent offline | Bitwarden Agent Access (`aac run`, Apache-2.0, early preview) adds human approval per credential; the Bitwarden MCP server returns passwords into the model's context |
| Website logins | Human logs in once; Playwright MCP `--storage-state .scratch/auth/<site>.json` or a dedicated profile | The state file is a bearer credential: 0600, delete after the task |
| GitHub | Free machine account plus a fine-grained PAT (selected repos, 30-day expiry) or a GitHub App (1-hour tokens) | Classic PATs reach every repo you can access |
| Protect your own MCP server | Keycloak (Apache-2.0) or Better Auth (MIT) as the authorization server; Cloudflare `workers-oauth-provider` (MIT) on Workers Free | Follow MCP auth 2026-07-28: audience check, PKCE, `iss` check, Client ID Metadata Documents |
| Gate internal tools | Pomerium (Apache-2.0) with upstream OAuth and `mcp_tool` deny rules, or Cloudflare Zero Trust Free (50 users) | Clients never see upstream tokens |
| Agents calling SaaS for users | Composio Hobby (100,000 tool calls a month) or Auth0 Free (25,000 MAU, Token Vault) | Provider tokens stay out of the model; the broker's own API key stays server-side |
| CI and cloud | GitHub OIDC to AWS, GCP, or Azure | No stored cloud keys |
| Scanning | gitleaks (MIT) pre-commit and in CI; GitHub push protection is free only for public repos | Private-repo push protection costs $19 per committer per month |

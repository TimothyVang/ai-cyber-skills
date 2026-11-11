# Secrets and .env for AI agents: free ways to store, share, and inject them

Summary (checked 2026-11-11):
- Best free pattern: the agent never holds the real value. Use a credential broker that swaps a placeholder for the real secret at the network edge: Claude Code sandbox `mask` mode, the Varlock proxy (MIT, local), or Infisical Agent Vault (MIT OSS binary, or cloud with 5,000 free brokered requests/month) ([Claude Code](https://code.claude.com/docs/en/sandboxing), [Varlock](https://varlock.dev/guides/proxy/), [Infisical](https://infisical.com/pricing)).
- To keep secrets in git, use dotenvx (BSD-3) or SOPS + age (MPL-2.0 / BSD-3). Each person or machine gets its own private key, kept in the OS keystore or outside the repo. Rotate the real credential when someone loses access ([dotenvx](https://github.com/dotenvx/dotenvx), [SOPS](https://github.com/getsops/sops), [age](https://github.com/FiloSottile/age)).
- Hosted free tiers that fit a solo dev or tiny team: Infisical (5 identities, MIT self-host), Bitwarden Secrets Manager (2 users, 3 projects, 3 machine accounts), Doppler (3 users), Phase (5 users or service accounts), Akeyless (5 clients). Give each agent its own scoped machine identity.
- Lock down the harness: in Codex set `inherit = "core"` and `ignore_default_excludes = false`. In Claude Code, add `sandbox.credentials` deny or mask entries, because `Read(./.env)` deny rules alone are bypassable. In MCP configs, reference env vars and never paste literal keys.

## Core rules

1. Order of preference: broker (agent holds a placeholder) > runtime injection into the app process only > encrypted file in the repo > plaintext `.env` that is gitignored. Never paste a value into a prompt, an MCP config, or an agent settings file [inference].
2. One identity per agent or per run, scoped to the fewest projects and environments, with the shortest TTL that works. Keep the orchestrator's credentials out of the agent's environment ([Infisical](https://infisical.com/docs/documentation/platform/agent-vault/how-it-works)).
3. Output redaction is defense in depth, not a boundary. Matching is exact, so transformed or derived values still leak ([dotenvx](https://dotenvx.com/docs/cli/run-redact/)).
4. In CI, prefer OIDC federation over stored long-lived secrets: "You won't need to duplicate your cloud credentials as long-lived GitHub secrets" ([GitHub](https://docs.github.com/en/actions/concepts/security/openid-connect)).
5. Removing someone's key does not revoke what they already decrypted. Rotate at the provider ([git-crypt README](https://github.com/AGWA/git-crypt), [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)).

## 1. Encrypted in the repo (.env committed as ciphertext)

| Tool | What it does | Free terms / license | Latest release | Agent-relevant notes | Source |
|---|---|---|---|---|---|
| dotenvx | Encrypts each value in `.env*` (secp256k1/ECIES). `dotenvx run -- cmd` decrypts just in time | BSD-3-Clause. Armor (hosted key custody, approvals, audit) is a separate product; see its page for pricing | v2.38.2, 2026-10-20 | Has first-party Claude, Codex, and Cursor guides. Private key lives in the OS secret store by default since 2.25.0, and in a file in non-interactive mode since 2.38.0 | [repo](https://github.com/dotenvx/dotenvx), [CHANGELOG](https://github.com/dotenvx/dotenvx/blob/main/CHANGELOG.md) |
| SOPS | Encrypts values in YAML/JSON/ENV/INI/binary with age, PGP, AWS/GCP/Azure KMS, or Vault/OpenBao | MPL-2.0. CNCF Sandbox (accepted 2023-05-17) | v3.13.3, 2026-07-23 (commits 2026-11-09) | Supports multiple recipients plus `updatekeys` and `rotate`. `sops exec-env` injects decrypted values without writing a file | [repo](https://github.com/getsops/sops), [CNCF](https://www.cncf.io/projects/sops/) |
| age | Small file-encryption tool and format. Recipients can be `age1...` keys or SSH `ssh-ed25519`/`ssh-rsa` keys | BSD-3-Clause | v1.3.2, 2026-08-29 | Recipients files list one key per line. Post-quantum support. YubiKey via `age-plugin-yubikey` | [repo](https://github.com/FiloSottile/age) |
| rage | Rust implementation of age | Apache-2.0 (GitHub metadata) | v0.12.1, 2026-07-14 | Same format, so it is a drop-in for age recipients | [repo](https://github.com/str4d/rage) |
| git-crypt | Transparent per-file encryption through git filters (GPG or a symmetric key) | GPL-3.0 | 0.8.0, 2025-09-24: **no release in 13+ months** | README: "does not support revoking access". Leaks file length and change patterns. Avoid for agent workflows | [repo](https://github.com/AGWA/git-crypt) |
| git-secret | GPG-encrypts files in the repo | MIT | v0.5.0, 2022-06-05: **releases stale** (commits 2026-09) | GPG only, so key distribution is heavy. Prefer SOPS + age | [repo](https://github.com/sobolevn/git-secret) |
| Varlock | `.env.schema` with `@sensitive` decorators, validation, redaction, leak scan, provider plugins, and a local credential proxy | MIT | Monorepo packages released 2026-10-29. Site lists 1.24.0 | Agents read the schema instead of the values. `varlock run --` injects. `varlock proxy run -- claude` gives the agent placeholders | [site](https://varlock.dev/), [repo](https://github.com/dmno-dev/varlock) |

dotenvx flow for agents ([README](https://github.com/dotenvx/dotenvx), [Claude guide](https://dotenvx.com/docs/claude/)):
```sh
dotenvx encrypt -f .env.production            # ciphertext is safe to commit; never commit .env.keys
dotenvx encrypt -f .env.production --with <public-key>   # encrypt with a key created elsewhere (no private key here)
DOTENV_PRIVATE_KEY_PRODUCTION=... dotenvx run -- node index.js   # CI: key comes from the CI secret store
dotenvx run --redact -- claude -p '...'        # v2.38.2: values become [REDACTED] in stdout/stderr
```
- Change on `main`, not yet released: `run --redact` is removed and redaction moves to a `Dotenvxfile` ("redacted true"). The `rotate` command was removed in 2.0.0 and is not back as of 2.38.2. Pin your version ([CHANGELOG](https://github.com/dotenvx/dotenvx/blob/main/CHANGELOG.md)).
- Redaction still gives the agent's child process the real value, so an agent that writes the value to a file or sends it over the network leaks it ([run --redact](https://dotenvx.com/docs/cli/run-redact/)) [inference].

SOPS + age multi-recipient setup, one key per person or machine ([age identity docs](https://github.com/getsops/docs/blob/main/content/en/docs/usage/identities/age/_index.md), [key management](https://github.com/getsops/docs/blob/main/content/en/docs/usage/key-management/_index.md)):
```yaml
# .sops.yaml
creation_rules:
  - path_regex: \.env(\..*)?\.enc$
    age: >-
      age1alice...,age1laptop2...,age1ci...
```
```sh
age-keygen -o ~/.config/sops/age/keys.txt     # Windows: %AppData%\sops\age\keys.txt; or SOPS_AGE_KEY_FILE / SOPS_AGE_KEY_CMD
sops encrypt --input-type dotenv --output-type dotenv .env > .env.enc
sops updatekeys .env.enc                       # add or remove recipients from .sops.yaml
sops rotate -i .env.enc                        # new data key; still rotate the real credentials
sops exec-env .env.enc 'npm start'             # inject into a child process, no plaintext file
```
- `SOPS_AGE_KEY_CMD` can fetch the key from a password manager, so the key file never sits next to the repo ([SOPS age docs](https://github.com/getsops/docs/blob/main/content/en/docs/usage/identities/age/_index.md)).

## 2. Secret managers with a free tier or free self-hosting

| Tool | What it does | Free terms / license | Latest release | Agent-relevant notes | Source |
|---|---|---|---|---|---|
| Infisical | Secrets manager plus CLI, daemon agent, machine identities, Agent Vault broker | Cloud Free: 5 identities (humans + machines), unlimited projects, 3 environments, 10 syncs. No versioning, rotation, or dynamic secrets. Core MIT; `ee/` is proprietary | Platform v0.167.8 and CLI v0.45.6, 2026-11-10 | `infisical secrets-manager run --` injects env. Machine identities log in for short-lived access tokens. The `infisical agent` daemon renders secrets to files | [pricing](https://infisical.com/pricing), [LICENSE](https://github.com/Infisical/infisical/blob/main/LICENSE), [CLI](https://infisical.com/docs/cli/reference-agents) |
| Bitwarden Secrets Manager | End-to-end encrypted secrets, projects, machine accounts, `bws` CLI | Free: unlimited secrets, 2 users, 3 projects, 3 machine accounts. Self-host is Enterprise only. SDK/CLI under the Bitwarden SDK License, which is source-available, not OSI open source | bws v2.1.0, 2026-05-21 | `bws run -- 'cmd'`, token in `BWS_ACCESS_TOKEN`. Docs warn not to run untrusted executables under `bws run` | [product](https://bitwarden.com/products/secrets-manager/), [CLI](https://bitwarden.com/help/secrets-manager-cli/), [license](https://github.com/bitwarden/sdk-sm/blob/main/LICENSE) |
| OpenBao | Community fork of Vault (KV, dynamic secrets, PKI, many auth methods) under LF OpenSSF | MPL-2.0, fully OSS | v2.7.2, 2026-10-26 | Free self-host. Dynamic DB/cloud creds and short-TTL tokens per agent. SOPS can use it as a key source | [site](https://openbao.org/), [repo](https://github.com/openbao/openbao) |
| HashiCorp Vault | Same feature family | **BSL 1.1 (source-available, not OSS)** for 1.15+. Production use is allowed except competitive hosted offerings | v2.2.1, 2026-10-22 | Prefer OpenBao if you want OSS | [LICENSE](https://github.com/hashicorp/vault/blob/main/LICENSE) |
| Doppler | SaaS secrets manager, `doppler run --` | Developer plan: free for 3 users ($8/mo per extra user), 50 service tokens, 10 projects, 4 environments, 3-day activity log. Service is proprietary; CLI is Apache-2.0 | CLI 3.77.1, 2026-10-22 | Billed per human seat: "AI agents and non-human identities ride free". Service accounts are Team-plan only | [pricing](https://www.doppler.com/pricing), [CLI docs](https://docs.doppler.com/docs/cli), [CLI repo](https://github.com/DopplerHQ/cli) |
| Phase | E2E-encrypted secrets manager, `phase run` | Cloud Free: 5 users or service accounts, 3 apps, 3 environments. Self-host Free: unlimited users and service accounts. Console MIT except `ee/`; CLI GPL-3.0 | Console v2.79.0, 2026-11-02; CLI v2.3.3, 2026-10-21 | Free tier lists "AI Agent Integration" and "Phase Agents Relay" (not evaluated here) [unverified] | [pricing](https://phase.dev/pricing), [console](https://github.com/phasehq/console), [CLI](https://github.com/phasehq/cli) |
| Akeyless | SaaS vault with gateway, dynamic and rotated secrets | Free: 5 clients, 500 static, 5 dynamic, 5 rotated secrets, 1 gateway cluster, 3-day audit. No SAML/OIDC/JWT auth on Free. Proprietary. Limits page last modified 2025-09-23 | n/a (SaaS) | A "client" is any identity that consumes secrets, so 5 agents use the whole free tier | [plan limits](https://www.akeyless.io/sla-support-tiers-and-plans-limits/) |
| 1Password (paid) | `op run --env-file` resolves `op://vault/item/field` references; service accounts | **Paid subscription.** Service accounts are immutable, rate-limited, and can be created with `--expires-in` | n/a | Masks secrets in output by default (`--no-masking` turns it off). Credential Broker for OIDC CI is in public preview | [service accounts](https://developer.1password.com/docs/service-accounts/get-started), [op run](https://developer.1password.com/docs/cli/secrets-environment-variables/) |
| AWS Secrets Manager | Cloud KV with rotation | $0.40/secret/month + $0.05 per 10,000 API calls. New accounts get up to $200 in free-tier credits | n/a | Pair with IAM roles or OIDC, not access keys in the agent env | [pricing](https://aws.amazon.com/secrets-manager/pricing/) |
| GCP Secret Manager | Cloud KV | Always-free: 6 active secret versions and 10,000 access operations/month. After that, $0.03 per 10,000 accesses and about $0.06/version/month [inference from hourly rate] | n/a | Workload identity federation avoids key files | [pricing](https://cloud.google.com/secret-manager/pricing) |
| Azure Key Vault | Cloud KV/HSM | Standard tier secrets operations are about $0.03 per 10,000 transactions [unverified: prices render client-side] | n/a | Use managed identity | [pricing](https://azure.microsoft.com/en-us/pricing/details/key-vault/) |

Injection commands (all start the child process with secrets as env vars; the agent can read them if it is the child):
```sh
infisical secrets-manager run --env=dev --path=/api -- npm start   # --token or INFISICAL_TOKEN for machine identities
bws run --project-id <id> -- 'npm run start'
doppler run -- your-command
op run --env-file=./prod.env -- your-command
phase run --env production 'npm start'                           # Phase CLI README
```
- Infisical `run` never injects `HOME`, `PATH`, `SHELL`, and similar names, and with `--watch` it restarts the command when secrets change ([CLI reference](https://infisical.com/docs/cli/reference-agents)).

## 3. Local OS stores and password-store CLIs (free, offline)

| Tool | What it does | License | Latest release | Agent-relevant notes | Source |
|---|---|---|---|---|---|
| Python `keyring` | One API over macOS Keychain, Freedesktop Secret Service (libsecret/GNOME), KWallet, and Windows Credential Locker | MIT | v25.7.0, 2025-11-16 | `keyring get svc user` in a launcher script keeps values out of files. Any process running as your user can usually read them [inference] | [repo](https://github.com/jaraco/keyring) |
| dotenvx native store | Stores dotenvx private keys in the OS secret store | BSD-3 | see above | `--no-native` turns off OS store lookups | [README](https://github.com/dotenvx/dotenvx) |
| `pass` | GPG-encrypted files in a git repo, one secret per file | GPL-2.0+ | Tag 1.7.4, 2021-06-11: **no release in 5 years** (commits through 2026-10) | Varlock has a `pass` plugin. GPG key handling is the cost | [mirror](https://github.com/zx2c4/password-store) |
| gopass | Team-oriented `pass` successor with recipients per store | MIT | v1.17.4, 2026-10-10 | Multi-recipient stores fit "share with agent machine X". Has gpg and age crypto backends (`docs/backends/age.md`) | [repo](https://github.com/gopasspw/gopass), [age backend](https://github.com/gopasspw/gopass/blob/master/docs/backends/age.md) |

## 4. Credential brokers: the agent never holds the secret

| Tool | How it works | Free terms / license | Latest | Limits | Source |
|---|---|---|---|---|---|
| Claude Code sandbox `credentials` | `deny` unsets env vars and blocks file reads for sandboxed Bash. `mask` shows a per-session sentinel; the sandbox proxy swaps in the real value only for `injectHosts` (re-signs AWS SigV4) | Included with Claude Code. Runtime Apache-2.0 | sandbox-runtime v0.0.82, 2026-11-09 | Needs `network.tlsTerminate`. Masks honored only from user/managed settings or `--settings`, not repo `.claude/`. Bash only; MCP servers and hooks run outside. **No sandbox on native Windows: use WSL2** | [sandboxing](https://code.claude.com/docs/en/sandboxing), [runtime](https://github.com/anthropics/sandbox-runtime) |
| Varlock proxy | Local in-memory proxy. The agent holds placeholders; real values go only to TLS-verified upstreams set with `@proxy(domain=...)` and are scrubbed from responses | MIT | see §1 | Same host, same user: "not a sandbox". Add `--sandbox` or a container or VM | [proxy guide](https://varlock.dev/guides/proxy/) |
| Infisical Agent Vault (cloud) | Orchestrator creates a time-bound session scoped to an access bundle. The proxy adds credentials, enforces method and path rules, and handles HTTP APIs, MCP servers, DBs, and SSH | First 5,000 brokered requests/month free, then $1 per 10,000 | Platform v0.167.8 | Run the proxy outside the agent's container and give the agent network access only to the proxy. Session tokens travel over plain HTTP, so use one proxy per agent on a private network | [how it works](https://infisical.com/docs/documentation/platform/agent-vault/how-it-works), [pricing](https://infisical.com/pricing) |
| Agent Vault OSS binary | Standalone HTTP credential proxy plus vault on local SQLite or Postgres: `agent-vault run -- claude` | MIT except `ee/` | v0.40.2, 2026-10-22 | README: "no longer recommended for new setups"; it points to the Infisical service | [repo](https://github.com/Infisical/agent-vault) |
| CyberArk Secretless Broker | Connection broker: the app connects to localhost and the broker authenticates to MySQL, Postgres, SSH (beta), or HTTP (beta) | Apache-2.0 | v2.0.0, 2026-09-16 | Built around Conjur and Kubernetes sidecars. Heavy for a single dev box | [repo](https://github.com/cyberark/secretless-broker) |
| omp auth broker | Keeps provider OAuth refresh tokens on a broker; clients get redacted snapshots and ask the broker to refresh | MIT (omp) | omp main, 2026-11-11 | Covers the model-provider credentials omp itself uses, not your app's secrets | [auth-broker doc](https://github.com/can1357/oh-my-pi/blob/main/docs/auth-broker-gateway.md) |

Claude Code user-level settings for masking (from [sandboxing](https://code.claude.com/docs/en/sandboxing)):
```json
{ "sandbox": { "enabled": true, "allowUnsandboxedCommands": false, "failIfUnavailable": true,
  "network": { "tlsTerminate": {}, "allowedDomains": ["*.github.com", "registry.npmjs.org"] },
  "credentials": {
    "files":   [ { "path": "~/.aws/credentials", "mode": "deny" }, { "path": "~/.ssh", "mode": "deny" } ],
    "envVars": [ { "name": "GH_TOKEN", "mode": "mask", "injectHosts": ["api.github.com"] },
                 { "name": "NPM_TOKEN", "mode": "deny" } ] } } }
```
- "There is no built-in credential deny list, so only the files and variables you list are restricted." The default sandbox read policy still allows `~/.ssh` and `~/.aws/credentials` ([sandboxing](https://code.claude.com/docs/en/sandboxing)).

## 5. How each harness handles env and MCP secrets

| Harness | Control | Default and caveat | Source |
|---|---|---|---|
| Codex | `[shell_environment_policy]`: `inherit = all/core/none`, `filters` (`"AWS_*" = "exclude"`, or include to allowlist), `set`. `ignore_default_excludes` | **Default `ignore_default_excludes = true`, so names containing KEY, SECRET, or TOKEN are passed to commands.** Set it to `false`. Legacy `exclude`/`include_only` arrays cannot be combined with `filters` in the same layer | [config-advanced](https://developers.openai.com/codex/config-advanced), [reference](https://developers.openai.com/codex/config-reference) |
| Codex MCP | `mcp_servers.<id>.env_vars` (allowlist for stdio), `bearer_token_env_var`, `env_http_headers`, `http_headers_helper` (command prints headers) | Project `.codex/config.toml` loads only for trusted projects and cannot redirect credentials or change provider auth | [config-advanced](https://developers.openai.com/codex/config-advanced), [reference](https://developers.openai.com/codex/config-reference) |
| Claude Code | `permissions.deny: ["Read(./.env)", "Read(./.env.*)"]` | Covers built-in file tools and recognized Bash readers (`cat`, `head`, redirects), but **not** `grep -r` or a Python/Node script that opens the file. For OS-level enforcement, enable the sandbox | [settings](https://code.claude.com/docs/en/settings), [permissions](https://code.claude.com/docs/en/permissions) |
| Claude Code | `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` | Strips credentials (matched by name or value) from Bash, hooks, and stdio MCP servers. Leaves GitHub tokens and proxy settings in place. On Linux it forces every command to run sandboxed | [env vars](https://code.claude.com/docs/en/env-vars), [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| Claude Code MCP | `.mcp.json` supports `${VAR}` and `${VAR:-default}` in `command`, `args`, `env`, `url`, `headers` | Commit `"Authorization": "Bearer ${API_KEY}"`, never the key itself | [mcp](https://code.claude.com/docs/en/mcp) |
| omp | Loads project `.env`, then `~/.omp/agent/.env`, `~/.omp/.env`, `~/.env`. Shell subprocesses have project-dotenv credentials filtered out | `secrets.enabled: true` (off by default) replaces secret-looking env values, `secrets.yml` entries, and built-in token patterns with HMAC placeholders before provider calls, and restores them in tool args | [env vars](https://github.com/can1357/oh-my-pi/blob/main/docs/environment-variables.md), [secrets](https://github.com/can1357/oh-my-pi/blob/main/docs/secrets.md) |
| omp MCP | `${VAR}` expansion; `"!cmd"` values run a command (10 s timeout) and use its stdout, re-run on 401/403; a bare var name copies from env | Use `"!cmd"` to mint short-lived tokens from `bws`/`op`/`infisical` [inference] | [mcp-config](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md) |
| MCP servers (spec) | Token passthrough is an anti-pattern. Servers must accept only tokens issued for themselves | Do not forward the client's token to downstream APIs | [MCP security](https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices) |

Codex hardening snippet ([config-advanced](https://developers.openai.com/codex/config-advanced)):
```toml
[shell_environment_policy]
inherit = "core"
ignore_default_excludes = false     # drop *KEY*, *SECRET*, *TOKEN* names
[shell_environment_policy.filters]
"AWS_*" = "exclude"
"AZURE_*" = "exclude"
```

## 6. Sharing between people, machines, and agents

| Need | Free approach | Notes | Source |
|---|---|---|---|
| Add a laptop, CI runner, or agent VM | Generate an age key on that machine; commit only its public key to `.sops.yaml`; run `sops updatekeys` | Private keys never travel. SSH ed25519 keys work as recipients | [SOPS key mgmt](https://github.com/getsops/docs/blob/main/content/en/docs/usage/key-management/_index.md), [age](https://github.com/FiloSottile/age) |
| dotenvx team | One keypair per env file. Share the private key out of band (password manager, `bws`, or `op`), or encrypt with `--with <public-key>` | Never commit `.env.keys`. No `rotate` command since 2.0.0, so re-key by hand | [README](https://github.com/dotenvx/dotenvx), [CHANGELOG](https://github.com/dotenvx/dotenvx/blob/main/CHANGELOG.md) |
| Hosted manager | One machine identity or account per agent and per environment, read-only, scoped to one project or path | Bitwarden Free caps at 3 machine accounts, Infisical Free at 5 identities total, Akeyless Free at 5 clients | [Bitwarden](https://bitwarden.com/products/secrets-manager/), [Infisical](https://infisical.com/pricing), [Akeyless](https://www.akeyless.io/sla-support-tiers-and-plans-limits/) |
| One-off handoff to a human | Infisical secret sharing (all plans) or Phase Lockbox links | Prefer expiring links over chat. 28% of incidents originate in Slack, Jira, or Confluence | [Infisical](https://infisical.com/pricing), [Phase](https://phase.dev/pricing), [GitGuardian](https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026) |
| Revocation | Remove the recipient (`sops updatekeys`), then `sops rotate`, **then rotate the upstream credential** | git-crypt cannot revoke at all. Old ciphertext stays in git history [inference] | [git-crypt](https://github.com/AGWA/git-crypt), [SOPS](https://github.com/getsops/docs/blob/main/content/en/docs/usage/key-management/_index.md) |
| Rotation cadence | Short-lived or dynamic credentials where possible (OpenBao, AWS STS via OIDC); otherwise scheduled rotation plus expiry | OWASP covers creation, rotation, revocation, and expiration as lifecycle stages | [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) |

## Threats and failure modes

- **Agent reads the file another way.** Claude Code `Read` deny rules don't stop `grep -r` or a script that opens `.env` itself ([permissions](https://code.claude.com/docs/en/permissions)). Only OS-level sandbox reads or a placeholder value close this gap.
- **Env inheritance.** Sandboxed commands inherit Claude Code's environment "including any secrets in its environment" unless `credentials` or `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` is set ([sandboxing](https://code.claude.com/docs/en/sandboxing)). Codex passes KEY/SECRET/TOKEN vars by default ([config-advanced](https://developers.openai.com/codex/config-advanced)).
- **Injectors expose plaintext to the child.** `bws run`, `op run`, `infisical run`, `dotenvx run`, and `sops exec-env` all put real values in the child's environment. If the child is the agent, the agent has the secret. Bitwarden warns against running untrusted executables under `bws run` ([bws](https://bitwarden.com/help/secrets-manager-cli/)).
- **Redaction gaps.** Exact-match only, so derived, encoded, or split values pass through ([dotenvx](https://dotenvx.com/docs/cli/run-redact/)). Response scrubbing in Varlock is "defense-in-depth, not a boundary" ([Varlock](https://varlock.dev/guides/proxy/)).
- **Same-user proxy bypass.** A local proxy that runs as you can be bypassed by an agent that spawns a process outside it ([Varlock](https://varlock.dev/guides/proxy/)). Infisical recommends running the proxy outside the agent's environment and limiting the agent's network to the proxy ([Infisical](https://infisical.com/docs/documentation/platform/agent-vault/how-it-works)).
- **Self-escalation.** If the agent can read the orchestrator's machine identity, "it could give itself more access" ([Infisical](https://infisical.com/docs/documentation/platform/agent-vault/how-it-works)).
- **Secrets in agent config files.** GitGuardian found 31,088 secrets in `.claude/settings.local.json` on public GitHub, 5,343 still valid ([GitGuardian](https://blog.gitguardian.com/claude-code-settings-local-json-secrets-docker-hub/)). It also found 24,008 secrets in MCP config files, 2,117 valid ([GitGuardian](https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026)).
- **AI-assisted commits leak more.** Claude Code-assisted commits leaked secrets at 3.2% vs a 1.5% baseline, and AI-service secret leaks rose 81% in 2025 ([GitGuardian](https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026)).
- **Prompt-injected exfiltration.** Untrusted content steers the agent into sending env or files to an attacker host. Mitigate with a domain allowlist, deny unsandboxed retries, and placeholders ([OWASP LLM02](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/), [OWASP Agentic Top 10](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), [sandboxing](https://code.claude.com/docs/en/sandboxing)).
- **Repo-controlled config loosening.** A cloned repo's settings could redirect credentials. Claude Code ignores repo `mask`/`tlsTerminate`, and Codex ignores untrusted project config ([sandboxing](https://code.claude.com/docs/en/sandboxing), [config-advanced](https://developers.openai.com/codex/config-advanced)).
- **Revocation illusion.** Re-encrypting without rotating the upstream credential leaves old copies valid; git-crypt has no revocation ([git-crypt](https://github.com/AGWA/git-crypt)).
- **MCP token passthrough.** A server forwards client tokens to downstream APIs without checking audience ([MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices)).
- **Windows gap.** Claude Code runs commands unsandboxed on native Windows, so credential masking and denies need WSL2 ([sandboxing](https://code.claude.com/docs/en/sandboxing)).

## Recommendation for a solo dev / small team, all free

1. **Source of truth.** Pick one:
   - SOPS + age: one age key per person, machine, and CI runner, listed in `.sops.yaml`.
   - dotenvx: private keys in the OS store, `.env.keys` gitignored.
   - Infisical Free (5 identities), or self-hosted Infisical, Phase, or OpenBao if you outgrow it.
2. **Agent sessions.** Start agents from a clean environment:
   - Codex: `inherit = "core"`, `ignore_default_excludes = false`.
   - Claude Code: in WSL2 or Linux/macOS, with `sandbox.enabled`, `allowUnsandboxedCommands: false`, `failIfUnavailable: true`, `credentials` denies for `~/.ssh` and `~/.aws`, and `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`.
   - omp: `secrets.enabled: true`.
3. **Secrets the agent must use** (GitHub, npm, APIs): broker them.
   - Claude Code `mask` with `injectHosts`, or `varlock proxy run -- <agent>` inside a container.
   - Infisical Agent Vault for headless or CI agents (5,000 free requests/month).
4. **Secrets only the app needs**: inject at the app's own process with `sops exec-env`, `dotenvx run`, `infisical secrets-manager run`, or `bws run`, outside the agent's shell. Let the agent read `.env.schema` or `.env.example` instead of the values.
5. **Identities**: one machine identity per agent, read-only, one environment, short TTL. In CI, use OIDC to the cloud instead of stored keys.
6. **MCP**: `${VAR}` references only. Gitignore `.claude/settings.local.json` and `.env*` except encrypted files. Scan before commit, for example with `varlock scan` or `dotenvx protect`.
7. **Offboarding or a suspected leak**: remove the recipient or identity, re-encrypt, rotate every upstream credential that person or agent could have seen, and revoke broker sessions.

# Logins, passwords, and MFA for AI agents: free options (checked 2026-11-11)

**Summary.** Best free setup: don't let the model read passwords at all. Reuse a session it is already signed in to (Playwright `storageState`, a persistent profile, or a relay into the user's own Chrome), or have a broker inject the credential into a child process or the page. Free broker: Bitwarden's open-source [Agent Access](https://github.com/bitwarden/agent-access) (`aac run`, human approval per request, still alpha). Paid broker that fills the page itself: [1Password for Agents](https://support.1password.com/1password-claude-security/).
Give agents their own accounts and short-lived tokens with narrow scopes: GitHub fine-grained PATs, GitHub App tokens that expire after 1 hour, device-flow logins. Never give an agent the TOTP seed or passkey for a human account.
Send secrets through stdin, not argv. Agent transcripts are saved to disk in plaintext (`~/.claude/projects`, `~/.codex/sessions`, `~/.omp/agent/sessions`), so any secret the model sees also ends up on disk.

## Rules
1. Order of preference: (a) the agent never sees the secret (the broker fills the page or injects env/stdin), (b) the agent uses a session cookie or OAuth token for its own account, (c) the agent reads a password from a vault. (c) is the last resort and only for low-value accounts [inference].
2. Avoid the "lethal trifecta": an agent with private data + untrusted content + a way to send data out can be tricked into exfiltrating it ([Willison](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)). Wiring a password vault into a browsing agent with network access creates exactly that ([kud/mcp-keepassxc README](https://github.com/kud/mcp-keepassxc)).
3. Use one account per agent and one vault/collection per agent, with expiring credentials, and give the agent only the minimum scopes it needs ([OWASP Secrets Mgmt](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)).
4. A human approves every credential release (Agent Access, 1Password, device flow, CIBA). Don't leave standing approvals in place.

## 1. Password managers an agent can use

| Tool | What it does | Free terms / license | Latest release | Agent-relevant notes | Source |
|---|---|---|---|---|---|
| Bitwarden (cloud) | E2EE password manager | Free plan: unlimited items and devices. A Free org shares with **1 other user, up to 2 collections**. Integrated TOTP is **Premium only** | n/a (SaaS) | A free 2-person org gives you a "human + agent account" split that costs nothing | [plans](https://bitwarden.com/help/password-manager-plans.md) |
| `bw` CLI | Full vault access from a shell; `--raw`, `--nointeraction`, `--passwordenv`, `--passwordfile` | GPL-3.0 (the `/bitwarden_license` dir is source-available) | cli-v2026.10.1, 2026-10-29 | `BW_SESSION` unlocks the **whole vault**; scope by using a dedicated agent account | [CLI docs](https://bitwarden.com/help/cli/), [license](https://github.com/bitwarden/clients/blob/main/LICENSE.txt) |
| `bw serve` | Local REST "Vault Management API" | same | same | Binds localhost:8087 and blocks requests that carry an `Origin` header. **Once unlocked it requires no auth**: any local process can list every item | [CLI docs](https://bitwarden.com/help/cli/), [issue #3932](https://github.com/bitwarden/clients/issues/3932) |
| `bitwarden/mcp-server` | Official MCP: list/get/create items, TOTP, Send, org admin | GPL-3.0, npm `@bitwarden/mcp-server` | v2026.7.0, 2026-07-07 | Passwords are returned **into the model context**. Local only, "never hosted publicly" | [README](https://github.com/bitwarden/mcp-server/blob/main/README.md) |
| Bitwarden Agent Access (`aac`) | E2EE tunnel: an agent requests one credential, a human approves it, and `aac run` injects it as env | Apache-2.0, free | v0.11.0, 2026-03-21 (alpha; commits still active) | Pairing token, then fetch by `--domain` or `--id`. The vendor says "early preview", so test it with sample data only | [repo](https://github.com/bitwarden/agent-access), [blog](https://bitwarden.com/blog/introducing-agent-access-sdk) |
| Vaultwarden | Unofficial Rust server compatible with the Bitwarden client API | AGPL-3.0, self-host, free | 1.37.5, 2026-11-01 | Org features at no cost. Works with `bw config server <url>`. Not affiliated with Bitwarden | [repo](https://github.com/dani-garcia/vaultwarden) |
| KeePassXC + `keepassxc-cli` | Local `.kdbx` vault; `show -s -a password`, `clip`, `-t` TOTP, key file/YubiKey unlock | GPL-2.0 or GPL-3.0, free | 2.8.0, 2026-10-21 | No server and no sync, so the file is the whole attack surface. Give the agent its own `.kdbx` | [man page](https://github.com/keepassxreboot/keepassxc/blob/develop/docs/man/keepassxc-cli.1.adoc) |
| KeePass MCP servers | Community wrappers | MIT/BSD | e.g. tuaris/keepassxc-mcp (4 stars, last push 2026-05) | All immature (fewer than 10 stars). One README's whole content is "Just don't." | [GitHub search](https://github.com/search?q=keepassxc+mcp&type=repositories), [kud/mcp-keepassxc](https://github.com/kud/mcp-keepassxc) |
| `pass` | GPG-encrypted files in git | GPL-2.0+, free | Last tag 1.7.4, **2021-06-11** (commits still land; last 2026-10-27) | No release in 5+ years. Prefer gopass | [repo](https://github.com/zx2c4/password-store) |
| gopass | pass-compatible store built for teams; GPG or age, git sync, multiple recipients, `otp` | MIT, free | v1.17.4, 2026-10-10 | `gopass env --stdin` keeps the secret out of env and `ps` | [repo](https://github.com/gopasspw/gopass), [env doc](https://github.com/gopasspw/gopass/blob/master/docs/commands/env.md) |
| Proton Pass | E2EE manager with `pass-cli run`/`inject` and `pass://` refs | Free: unlimited logins, 2 vaults, share with 2 others. **CLI and integrated 2FA are paid (Pass Plus)**. CLI is GPL-3.0 | pass-cli 2.7.0, 2026-11-03 | `run` masks secrets in stdout/stderr by default. MCP servers are community-built only | [pricing](https://proton.me/pass/pricing), [run doc](https://github.com/protonpass/pass-cli/blob/main/docs/public/docs/commands/contents/run.md) |
| 1Password (paid) | Secure Agentic Autofill / "1Password for Agents"; service accounts; Environments | **Paid** (from $3.99/mo, 14-day trial) | n/a | The agent gets metadata only. A human approves each session and values are filled into the page | [pricing](https://1password.com/pricing/password-manager), [security](https://support.1password.com/1password-claude-security/) |

**Bitwarden MCP security model** ([README](https://github.com/bitwarden/mcp-server/blob/main/README.md)):
- `unlock` takes no parameters. It opens a native OS password dialog (osascript, zenity/kdialog, or a PowerShell WinForms dialog).
- The master password reaches `bw unlock` through a one-shot random env var, so it "never appears in process arguments, in the MCP protocol, or in the LLM's context".
- On headless machines `unlock` refuses to run, and you put `BW_SESSION` in the MCP config by hand. That session key unlocks the whole vault.
- File tools are disabled unless `BW_ALLOWED_DIRECTORIES` is set.
- Limits: `get` returns passwords and TOTP codes to the model, and org-admin tools can invite or remove members. The README warns that "AI responses may inadvertently reveal sensitive information" and suggests self-hosted or local LLMs for sensitive data.

**Agent Access flow** ([repo](https://github.com/bitwarden/agent-access)). The protocol "is open for any credential provider". OneCLI integration is live and a Browserbase integration is "in development" ([blog](https://bitwarden.com/blog/introducing-agent-access-sdk)):
```bash
aac listen                                   # human side: unlock bw, print a pairing token
aac connect --token <pairing-token> --output json            # agent side: pair once
aac run --domain example.com --env DB_PASSWORD=password --env DB_USER=username -- psql
```
Prefer `aac run`: `aac connect --output json` prints the password to stdout, so the model sees it.

**1Password for Agents (paid, brief)** ([security model](https://support.1password.com/1password-claude-security/)):
- Pairing checks OS code signing against a partner allowlist. Each agent session gets its own crypto credentials, and each request triggers a desktop approval prompt with no standing approvals.
- Approved items are cached AES-256-GCM in browser-extension memory for at most 9 hours. The agent "sleeps" while the form is filled and submitted, and fields are cleared if submission fails.
- Browserbase integration shipped 2026-10-22 ([changelog](https://www.browserbase.com/changelog/1password-for-agents)).
- Accepted risk, in 1Password's own words: once signed in, "what the agent does on the website is governed by the agent product's own safeguards".

## 2. Reuse sessions instead of handing over passwords

| Tool | What it does | Free terms / license | Latest release | Agent-relevant notes | Source |
|---|---|---|---|---|---|
| Playwright `storageState` | Saves cookies, localStorage, IndexedDB, and passkey state to JSON and reloads it | Apache-2.0 | v1.65.0, 2026-11-05 | Vendor: the file "may contain sensitive cookies... could be used to impersonate you". Keep it in a gitignored `playwright/.auth` | [auth docs](https://playwright.dev/docs/auth) |
| Playwright MCP | Browser MCP with persistent or isolated profiles | Apache-2.0 | v0.0.85, 2026-11-09 | `--user-data-dir`, `--isolated --storage-state=...`, `--extension` (attach to the user's Chrome), `--secrets <dotenv>`, `--redact-url-params` | [README](https://github.com/microsoft/playwright-mcp) |
| Chrome DevTools MCP | CDP-based MCP for Chrome | Apache-2.0 | v1.13.0, 2026-11-11 | `--isolated` (temp profile), `--user-data-dir`, `--autoConnect` (Chrome 144+, user enables remote debugging), `--browser-url` | [config](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/configuration.md) |
| browser-use | Python browser agent | MIT | 1.0.2, 2026-11-11 | `sensitive_data` scoped by domain; `type_secret()` types values the model never sees; `storage_state` / Chrome profile reuse | [secrets](https://docs.browser-use.com/open-source/secrets.md) |
| Browserbase Contexts | Hosted browser profile (cookies, localStorage, IndexedDB) reused across sessions | Free plan: 1 browser-hour, 3 concurrent, 15-min sessions, 7-day retention. Paid from $20 | n/a (SaaS) | Contexts are "encrypted at rest" and "live indefinitely" until deleted. The official MCP repo was **archived** (last release v3.0.0, 2026-03-31) | [plans](https://docs.browserbase.com/account/billing/plans), [contexts](https://docs.browserbase.com/platform/browser/core-features/contexts), [MCP repo](https://github.com/browserbase/mcp-server-browserbase) |
| omp browser relay | Drives the user's real, already-signed-in Chrome through an extension plus a local CDP relay | Ships with omp | n/a | Binds loopback; use `--token` if other local processes are untrusted. Cannot attach to DevTools-open or internal tabs | omp docs (`omp://user-facing-packages.md`, `omp://tools/browser.md`) |

Rules for session reuse:
- A saved state file or profile directory is a **bearer credential**. Treat it like a password: give it 0600 perms, keep it in the project's self-ignored `.scratch/auth/`, and delete it when the task ends ([Playwright](https://playwright.dev/docs/auth)).
- Prefer a separate profile signed in as the **agent's own** account. Use relay or `--extension` into your personal browser only for supervised, interactive tasks, because the agent then holds every session you have open [inference].
- Chrome 136+ ignores `--remote-debugging-port` on the **default** profile. Infostealers used it to pull cookies, so a non-default `--user-data-dir` is now required ([Chrome blog](https://developer.chrome.com/blog/remote-debugging-port)). Don't try to work around it.
- Playwright MCP's `secrets`/`redactUrlParams` "is a convenience and not a security feature" ([README](https://github.com/microsoft/playwright-mcp)). browser-use redaction skips **screenshots**, and code the model writes "can read" the values ([browser-use](https://docs.browser-use.com/open-source/secrets.md)).

```bash
# one-time human login, then the agent reuses the state in an isolated context
npx @playwright/mcp@latest --isolated --storage-state=.scratch/auth/site.json
# Chrome DevTools MCP with a throwaway profile
npx chrome-devtools-mcp@latest --isolated
```

## 3. CLI logins, keychains, and OAuth device flow

| Tool | Login method for headless agents | Where the credential lives | Source |
|---|---|---|---|
| `gh` | Browser or device code; `--with-token` reads stdin; `GH_TOKEN` env for fine-grained PATs; `--expiring` prefers auto-refreshed tokens | OS credential store; **falls back to a plaintext file** if none is available (`--insecure-storage` forces it) | [gh auth login](https://cli.github.com/manual/gh_auth_login) |
| `aws sso login` | PKCE by default (2.22.0+); `--use-device-code` for another device | `~/.aws/sso/cache` on disk | [AWS docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html) |
| `gcloud auth login` | `--no-browser` (finish on a second machine) or `--no-launch-browser` (paste URL) | gcloud config dir [unverified path details] | [gcloud ref](https://cloud.google.com/sdk/gcloud/reference/auth/login) |
| `az` | MSAL | Token cache **encrypted on Windows, plaintext on Linux/macOS** | [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/msal-based-azure-cli) |
| OAuth 2.0 Device Authorization Grant | The agent shows a `user_code` + `verification_uri`; a human approves on another device; the agent polls (default 5 s) | Token held by the agent | [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628) |

- These CLIs keep refresh tokens readable by any process running as the same OS user, and the agent runs as that user. If an agent runs in your shell, it inherits every cloud login you have. Use a separate OS user, container, or profile (`AWS_PROFILE`, `CLOUDSDK_CONFIG`, `GH_CONFIG_DIR`) per agent [inference].
- Device flow is the right fit for headless agents because the human authenticates on their own device. Mitigate remote phishing (an attacker starting the flow and sending you the code) by always checking the `user_code` and keeping its lifetime short ([RFC 8628 s5.4](https://www.rfc-editor.org/rfc/rfc8628#section-5.4)).

## 4. MFA, TOTP, passkeys, and human approval

- **TOTP seeds.** Whoever holds an RFC 6238 seed can mint valid codes ([RFC 6238](https://www.rfc-editor.org/rfc/rfc6238)), so an agent holding both password and seed turns 2FA into one factor [inference].
  - Never give an agent the seed for a human or admin account. Seeds are acceptable only for a dedicated, low-privilege agent or test account.
  - Even then, use a broker that types the code without exposing the seed. browser-use secrets ending in `bu_2fa_code` type "the current 6-digit code, never the seed" ([browser-use](https://docs.browser-use.com/open-source/secrets.md)). 1Password fills OTPs after approval ([1Password](https://support.1password.com/1password-claude-security/)).
  - Bitwarden's MCP `get` returns TOTP codes into context ([README](https://github.com/bitwarden/mcp-server/blob/main/README.md)). Integrated TOTP code generation in Bitwarden requires Premium ([plans](https://bitwarden.com/help/password-manager-plans.md)).
- **Passkeys/WebAuthn.** A real authenticator needs a human gesture (user presence), so a production passkey for a human account can't be driven headlessly [inference].
  - The spec defines automation only as a WebDriver virtual-authenticator extension "for the purposes of user agent automation and web application testing" ([WebAuthn L2 s11](https://www.w3.org/TR/webauthn-2/#sctn-automation)).
  - Playwright's `context.credentials` (v1.61+) is a software virtual authenticator. Its `get()` returns credentials that include the private key, so they can be saved to disk and re-seeded ([Playwright](https://playwright.dev/docs/api/class-credentials)).
  - That turns the passkey into an ordinary file secret. Use it only for test accounts on test relying parties [inference].
- **Human-in-the-loop patterns:**
  - Approval for each credential: Agent Access CLI approval ([repo](https://github.com/bitwarden/agent-access)), or the 1Password desktop prompt with no standing approvals ([1Password](https://support.1password.com/1password-claude-security/)).
  - Push approval to the human's phone via OpenID **CIBA**. The client starts auth with a `login_hint`, a `binding_message` is shown on both devices, and tokens are delivered by poll, ping, or push ([CIBA Core 1.0](https://openid.net/specs/openid-client-initiated-backchannel-authentication-core-1_0.html)).
  - Device flow: the human approves on their own device while the agent polls ([RFC 8628](https://www.rfc-editor.org/rfc/rfc8628)).
  - The human does the MFA step in a relay tab or Browserbase live view, then the agent reuses the session (section 2) ([Browserbase contexts](https://docs.browserbase.com/platform/browser/core-features/contexts)).

## 5. Dedicated agent accounts and least privilege

| Mechanism | Free? | Scope and lifetime | Source |
|---|---|---|---|
| GitHub machine account | Free; ToS allows **one free machine account** per person, "used exclusively for performing automated tasks" | You remain responsible for its actions | [GitHub ToS](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) |
| GitHub fine-grained PAT | Free | One owner, selected repos, per-permission read/write, expiry 1-366 days (default 30). Max 50 tokens. Some features still need classic PATs | [PAT docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) |
| GitHub App installation token | Free | Per-installation permissions; **expires after 1 hour** | [App token docs](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app) |
| Test accounts | Free | Created per test or per worker, never production users | [Playwright auth](https://playwright.dev/docs/auth) |
| Bitwarden free org | Free (2 users, 2 collections) | Put only the agent's items in a collection the agent account can read | [plans](https://bitwarden.com/help/password-manager-plans.md) |

Rules: classic PATs reach "every repository that you can access", so avoid them ([GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)). Name the agent in the account or token so audit logs show which actions were the agent's [inference]. Revoke and rotate immediately after any exposure ([OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)).

## 6. Passing secrets to commands safely

Exposure ranking, safest first: **stdin or file descriptor**, then a 0600 or ramdisk file, then an env var in a child process, then argv [inference from the sources below].
- **argv** shows up in `/proc/<pid>/cmdline` and `ps` for other users unless `/proc` is mounted with `hidepid` ([proc(5)](https://man7.org/linux/man-pages/man5/proc.5.html)). It also ends up in shell history and in the agent transcript as part of the tool call.
- **env**: `/proc/<pid>/environ` needs ptrace-read rights ([proc_pid_environ(5)](https://man7.org/linux/man-pages/man5/proc_pid_environ.5.html)), meaning the same user or root, and therefore the agent itself. gopass warns that env injection is visible "for the entire lifetime of the subprocess" ([gopass env](https://github.com/gopasspw/gopass/blob/master/docs/commands/env.md)).
- **stdin** keeps secrets "from ending up in the shell's history, or log-files" ([docker login](https://docs.docker.com/reference/cli/docker/login/)).

```bash
bw get password agent-db --raw | docker login -u agentbot --password-stdin   # bw reads BW_SESSION from env; `--session <key>` would put it in argv
gopass env --stdin db/password gpg --passphrase-fd 0 --decrypt file.gpg
gh auth login --with-token < .scratch/auth/gh-token              # 0600 file a human placed, not `echo TOKEN |`
pass-cli run --env-file .env -- ./deploy.sh                       # .env holds pass:// refs; output masked by default
export BW_SESSION="$(bw unlock --raw --passwordfile .scratch/auth/mp)"   # key goes into a var, not stdout; vendor: file readable by one user only
```
Shell tips [inference]:
- In bash, `printf '%s' "$X" | cmd` and `echo "$X" | cmd` keep the value out of any process's argv, because `printf` and `echo` are builtins and never exec a separate program.
- An inline literal like `echo ghp_xxx | cmd` still leaks: the token lands in shell history and in the agent transcript as part of the tool call.
- Have the agent call a wrapper script that fetches and pipes the secret itself, so the value never appears in a model-authored command.

**Transcripts keep whatever the model sees, in plaintext:**

| Agent | Where | Retention / control | Source |
|---|---|---|---|
| Claude Code | `~/.claude/projects/` | Plaintext, **30 days** by default; `cleanupPeriodDays` changes it; Desktop/Cowork sessions exempt by default | [data usage](https://code.claude.com/docs/en/data-usage) |
| Codex CLI | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`; `~/.codex/history.jsonl` | `[history] persistence = "none"` turns off history and `max_bytes` caps it. Whether that also stops `sessions/` rollouts is [unverified] | [config](https://developers.openai.com/codex/config-advanced), [recorder.rs](https://github.com/openai/codex/blob/main/codex-rs/rollout/src/recorder.rs) |
| omp | `~/.omp/agent/sessions/<encoded-cwd>/<ts>_<id>.jsonl` (plus subagent transcripts) | `omp gc` compresses; delete the files to purge | omp docs (`omp://session.md`) |

If a secret reaches context, assume it is on disk and possibly at the model provider: **rotate it, don't just delete the file** ([OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)). Output masking is helpful but not a boundary: `pass-cli run` masks by default ([run doc](https://github.com/protonpass/pass-cli/blob/main/docs/public/docs/commands/contents/run.md)), Playwright MCP says redaction is "not a security feature".

## Threats and failure modes
- **Prompt injection, then a vault read, then exfiltration.** Any agent that holds vault tools plus browsing or fetch can be steered by page or email text ([Willison](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)). Bitwarden's MCP README: AI responses "may inadvertently reveal sensitive information" ([README](https://github.com/bitwarden/mcp-server/blob/main/README.md)).
- **Unauthenticated local vault API.** An unlocked `bw serve` answers any local process, or the whole network with `--hostname all`. Bitwarden's response: "not intended to be used outside of a tightly controlled environment" ([#3932](https://github.com/bitwarden/clients/issues/3932), [CLI docs](https://bitwarden.com/help/cli/)).
- **`BW_SESSION` in MCP config files.** The session key unlocks the whole vault, and config files get committed or shared, which the README explicitly warns against ([README](https://github.com/bitwarden/mcp-server/blob/main/README.md)).
- **Session files are as good as passwords.** `storageState` JSON, profile dirs, Browserbase contexts, and Playwright passkey JSON all let someone impersonate the account ([Playwright](https://playwright.dev/docs/auth), [Credentials](https://playwright.dev/docs/api/class-credentials), [Browserbase](https://docs.browserbase.com/platform/browser/core-features/contexts)).
- **Cookie theft via remote debugging.** The reason Chrome locked down the default profile ([Chrome](https://developer.chrome.com/blog/remote-debugging-port)). A CDP port left open on your real profile, or a relay without `--token` on a shared machine, does the same thing [inference].
- **Redaction gaps.** Screenshots, model-written code, files the agent writes, and short values (<4 chars) are not redacted ([browser-use](https://docs.browser-use.com/open-source/secrets.md)).
- **Transcript persistence.** 30-day plaintext Claude Code transcripts and Codex rollouts keep every secret the model saw ([Claude](https://code.claude.com/docs/en/data-usage), [Codex](https://developers.openai.com/codex/config-advanced)).
- **Inherited CLI logins.** gh falls back to plaintext storage, the az cache is plaintext on Linux/macOS, and AWS SSO tokens are cached on disk ([gh](https://cli.github.com/manual/gh_auth_login), [az](https://learn.microsoft.com/en-us/cli/azure/msal-based-azure-cli), [aws](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)).
- **Device-code phishing.** An attacker starts the flow and gets the user to approve it ([RFC 8628 s5.4](https://www.rfc-editor.org/rfc/rfc8628#section-5.4)).
- **Over-broad tokens.** Classic PATs, shared human accounts, or TOTP seeds handed to the agent, which defeats the point of 2FA ([GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)).
- **Immature community bridges.** KeePass, Proton, and Vaultwarden MCP servers are single-maintainer projects with few stars; one vendor MCP repo (Browserbase) is archived ([search](https://github.com/search?q=keepass+mcp&type=repositories), [Browserbase MCP](https://github.com/browserbase/mcp-server-browserbase)).

## Recommendation for a solo dev / small team, all free
1. **Vault:** Bitwarden free (or self-hosted Vaultwarden, AGPL). Create a separate **agent account**, join it to your free 2-person org, and share it only one "agent" collection ([plans](https://bitwarden.com/help/password-manager-plans.md)). Fully offline alternative: one `.kdbx` per agent with KeePassXC, or gopass with an age recipient just for the agent.
2. **Delivery:** use `aac run` (Agent Access) or `bw get ... --raw | cmd --password-stdin` inside a wrapper script, so the agent calls the wrapper and never prints the value. Don't use `bw serve`, and don't put `BW_SESSION` in shared MCP configs. Use the Bitwarden MCP server only with a vault that holds nothing but the agent's own low-value items.
3. **Web logins:** a human logs in once, then the agent works from a Playwright `storageState` or a dedicated `--user-data-dir` signed in as the agent account. Use the omp relay or `--extension` only for supervised work in your real browser.
4. **APIs and GitHub:** fine-grained PAT (select repos, 30-day expiry) or a GitHub App, held by the machine account. Cloud CLIs use device or `--no-browser` login under a separate profile/config dir.
5. **MFA:** keep TOTP seeds and passkeys for human accounts with humans. Agent test accounts can use a brokered TOTP (`bu_2fa_code`) or Playwright virtual passkeys. For anything higher-stakes, the human approves (device flow, push, or Agent Access prompt).
6. **Hygiene:** pass secrets over stdin, not argv. On machines that handle secrets, set `cleanupPeriodDays` low and Codex `history.persistence = "none"`, and prune `~/.codex/sessions` and `~/.omp/agent/sessions`. Rotate any secret that appeared in a transcript.

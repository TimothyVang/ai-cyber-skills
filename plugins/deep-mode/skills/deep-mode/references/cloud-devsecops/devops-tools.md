# DevOps tooling picks (DevOps Toolbox channel)

Read when choosing terminal, shell, multiplexer, editor, git, container, Kubernetes, Terraform, local cloud emulation, observability, secrets, or code-review tooling, or when setting up an agent's local dev loop. Every verdict here is one creator's opinion (the DevOps Toolbox YouTube channel, host Omer), gathered from 174 videos as of 2026-11-11. They are not vendor facts or independent benchmarks; numbers are the creator's claims. Cloud-specific security lives in `aws.md`, `azure.md`, `gcp.md`; pipeline rules in `devsecops-pipeline.md`.

Full report: https://github.com/TimothyVang/cloud-devsecops/blob/main/research/devopstoolbox-channel.md

## Strongest recommendations

1. Local AWS: [Floci](https://github.com/floci-io/floci) (MIT) instead of LocalStack. Claimed 24 ms start, ~13 MB RAM, 19 MB image versus LocalStack's >3 s, ~150 MB, >1 GB.
2. Learn Terraform even if AI writes it: read every plan, use remote locked state, apply only a saved plan. OpenTofu is a drop-in with state encryption.
3. Open-source AI PR review ([PR-Agent](https://github.com/The-PR-Agent/pr-agent)) instead of SaaS reviewers. The creator runs it in GitHub Actions; deep-mode runs it locally through its **pr-agent** technique and needs no Actions or hosted review service.
4. Encrypt `.env` with [dotenvx](https://github.com/dotenvx/dotenvx); keep `.env.keys` out of git and the Docker build context.
5. [Gitleaks](https://github.com/gitleaks/gitleaks) as a CI circuit breaker, including dangling git objects; [Trivy](https://github.com/aquasecurity/trivy) on images and lockfiles before push.
6. Short-lived JIT credentials (Teleport, Descope) for humans and agents; no static keys in agent configs.
7. Dockerfile discipline: slim/distroless not Alpine, cache-friendly layer order, `.dockerignore`, digest pinning.
8. Question Kubernetes first: Swarm, Kamal, or one VPS with Compose often suffices.
9. Sandbox autonomous agents (containers, Lima VMs, worktrees) and gate them (OpenSpec, Babysitter).
10. Linear history: rebase, `--ff-only`, `--force-with-lease`.
11. License-safe forks: OpenTofu > Terraform, Valkey > Redis, Podman > Docker Desktop, Angie > Nginx Plus.
12. Lightweight first: Dozzle for logs, Postgres/SQLite before specialized databases.

## Terminal and shell

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| Ghostty | GPU terminal | Daily driver; near-zero config; `ghostty +show-config --default --docs` | WezTerm, Alacritty, iTerm2 |
| Warp | AI terminal with blocks | Good for teams wanting batteries included | macOS Terminal |
| Zsh + Starship | Shell + TOML prompt | Daily driver; vi mode `bindkey -v` | Bash, Oh My Zsh themes, Powerlevel10k |
| Nushell | Structured-data shell | Great for JSON/YAML; abandoned as login shell (not POSIX, no `eval`) | jq/yq/awk pipelines |
| Atuin | SQLite shell history with sync | On every machine; `Ctrl+R` | `.zsh_history` |
| Zoxide | Learning `cd` (`z`, `zi`) | "Most important CLI" | `cd` |
| FZF | Fuzzy finder | "King of CLIs"; `Ctrl+R`, `Ctrl+T`, `Alt+C`, `**<Tab>` | Linear search |
| Mise | Runtimes, env, tasks in `mise.toml` | "Holy grail" | asdf, nvm, direnv, Makefiles |
| Carapace | Multi-shell completions | Recommended for kubectl/aws/git | Default completions |

Aliases the creator uses: `k`=kubectl, `tf`=terraform/tofu, `l`=`eza --icons --git`.

## Multiplexers

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| tmux | Multiplexer | Core; prefix `Ctrl-A`, TPM, index from 1 | screen |
| Sesh | Session manager with `sesh.toml` templates | Rated above SessionX | tmuxinator |
| tmux-sessionx / tmux-floax | FZF session picker / floating scratch pane | Creator's own, used daily | `prefix+s`, split juggling |
| Workmux | Worktree + agent status sidebar in tmux | Brilliant for agent visibility | Manual worktrees |
| Zellij | Rust multiplexer | Decent; lacked session resurrection | — |
| CMUX | libghostty multiplexer | Overhyped for tmux users | — |

## Editors

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| Neovim + LazyVim | Main IDE | 10+ years daily | VS Code, JetBrains |
| Telescope, Mason, Trouble, Harpoon, Snacks | Picker, LSP installs, diagnostics, jumps | All recommended | NERDTree, manual installs |
| vim-dadbod-ui | DB client in editor | Excellent | DBeaver, pgAdmin |
| nvim-dap | Debugger | Recommended | Print debugging |
| Zed | Fast Rust editor with agents | Kept alongside Neovim | Cursor, VS Code |

## Git and code review

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| [LazyGit](https://github.com/jesseduffield/lazygit) | Git TUI | "Gold standard" | Git GUIs |
| Jujutsu (jj) | Git-compatible VCS, no staging | "Fundamentally better"; `jj git init --colocate` | Stash/rebase pain |
| [Worktrunk](https://github.com/max-sixty/worktrunk) (`wt`) | Worktrees (`wt switch -c`, `wt merge`) | Essential | Raw `git worktree`, stash |
| gh-dash + Octo.nvim | PRs/issues in terminal and Neovim | Indispensable | GitHub web UI |
| Twik/tweaker | Review TUI that submits to GitHub/GitLab | "The missing piece" | Browser review |
| [PR-Agent](https://github.com/The-PR-Agent/pr-agent) | OSS AI reviewer (creator: in Actions; deep-mode: local, **pr-agent** technique) | Adopted | Hosted AI reviewers on private repos |
| Hosted AI reviewer | SaaS AI reviewer | Good at layering huge AI PRs; deep-mode's **pr-review** replaces it | — |

PR-Agent `.pr_agent.toml`:

```toml
[config]
allow_dynamic_context = true
[pr_code_suggestions]
commitable_code_suggestions = true
```

Git habits: `git rebase -i` before push; `git push --force-with-lease`; merge with `--ff-only` (merge-button commits rerun CI and builds); `git config rerere.enabled true`.

## Containers

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| Podman / Podman Desktop | Rootless daemonless engine; `podman generate kube` | Strongly recommended; free commercially | Docker Desktop |
| [LazyDocker](https://github.com/jesseduffield/lazydocker) | Docker TUI | Essential | `docker ps/logs/exec` |
| Lima | Linux VMs on macOS | Best Mac VM; good agent sandbox | Docker Desktop VM |
| Docker Swarm | Small-scale orchestration | Underrated for small prod | Kubernetes |
| Buildpacks (`pack build`) | Images without Dockerfile | Clean defaults | Dockerfiles |

Dockerfile pattern:

```dockerfile
FROM node:22-slim@sha256:<digest>   # get digest: docker buildx imagetools inspect node:22-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
USER node
```

- Alpine's musl forces source builds of native deps (slim built up to 15× faster in the creator's test). Prefer distroless over `scratch` (CA certs, tzdata, non-root user).
- Always ship a `.dockerignore` (include `.env`, `.env.keys`, `.git`).

Debugging:

```bash
docker init                 # scaffold multi-stage Dockerfile, .dockerignore, compose
docker diff <ctr>           # A/C/D filesystem changes
docker cp <ctr>:/path .     # works on stopped containers too
docker update --cpus 2 <ctr># live resource change; raising memory limit needs recreate
docker compose up -d --no-deps <svc>   # redeploy one service
```

VPS ops: layer `compose.prod.yaml` (use `!reset`), wrap the stack in a systemd unit with `Restart=always`.

## Kubernetes

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| [k9s](https://github.com/derailed/k9s) | Cluster TUI | Mandatory | `kubectl get/describe` |
| [stern](https://github.com/stern/stern) | Multi-pod log tail | Indispensable | `kubectl logs` |
| kubectx/kubens | Context/namespace switch | Game changer | `kubectl config` |
| k3s / k3d | Light Kubernetes | Go-to for local, edge, homelab | Heavy distros |
| Helm | Packages | Standard | Raw YAML |
| Kubebuilder | Operators/CRDs | Recommended | Hand-written controllers |
| Traefik | Ingress | Replacement for retired ingress-nginx; translates annotations, ACME | ingress-nginx |

```bash
k3d cluster create dev -p "8081:80@loadbalancer"   # local cluster in <20 s
kubectl auth can-i list secrets --as=system:serviceaccount:app:sa   # verify least privilege
kubectl autoscale deployment web --cpu-percent=50 --min=1 --max=10  # needs metrics-server
```

Adopt Kubernetes only for a real need (autoscaling, multi-node rescheduling); otherwise Swarm, Kamal, or a VPS is cheaper.

## Terraform / IaC

```bash
terraform plan -out=tfplan   # review the plan, including dependency chains
terraform apply tfplan       # applies exactly what was reviewed
terraform destroy            # reverse-order teardown; avoids orphaned NAT gateways/EIPs
```

- Remote state in S3 with locking; never local `.tfstate` in production.
- AI emits hundreds of HCL lines fast; blind apply can delete VPCs, load balancers, DNS.
- [OpenTofu](https://github.com/opentofu/opentofu): Linux Foundation drop-in (`alias tf=tofu`) with native state encryption.
- Amazon Q Developer CLI + AWS Labs MCP servers (Terraform, cost): creator's pick for AWS Terraform review and cost estimates.
- Coder: ephemeral dev environments from Terraform templates.

## Local cloud emulation (Floci)

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| [Floci](https://github.com/floci-io/floci) ([site](https://floci.io/aws/)) | Local AWS on `localhost:4566`, web dashboard; creator also mentions GCP/Azure | "Outstanding" | LocalStack |

```bash
floci start
eval $(floci env)   # fake credentials + endpoint for the AWS CLI/SDKs
```

```hcl
provider "aws" {
  region                      = "us-east-1"
  skip_credentials_validation = true
  endpoints {
    s3  = "http://localhost:4566"
    sqs = "http://localhost:4566"
    eks = "http://localhost:4566"
  }
}
```

More detail on Floci: `local-emulators.md`. Cost traps the creator flags: S3 event → Lambda writing back to the same bucket loops forever; S3 bills grow on egress, not storage; stopped EC2 still pays for EBS.

## CI/CD

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| Gitleaks + Trivy | Secret and CVE gates | Mandatory | Manual audits |
| PR-Agent | AI review (deep-mode runs it locally) | Adopted | SaaS reviewers |
| Kestra | YAML workflow orchestration | Underrated | Airflow, cron, Jenkins |
| Depot | Remote build cache, faster runners | Claimed up to 40× faster builds (channel sponsor) | Cold runners |

Deploy the commit hash CI verified: linear rebased history makes that true.

## Secrets and access

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| [dotenvx](https://github.com/dotenvx/dotenvx) | Encrypted `.env` | Good security/convenience balance | Plaintext `.env` |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | Secret scanning | Mandatory CI breaker | Post-leak panic |
| [Trivy](https://github.com/aquasecurity/trivy) | Image/lockfile/misconfig scanning | Essential | Unscanned images |
| [Infisical](https://github.com/Infisical/infisical) | Self-hosted E2E secrets manager, injects at container start | Obvious choice for homelab and prod | Scattered `.env` |
| Teleport | Short-lived certs for SSH/K8s/DB | Removes static creds | Long-lived keys |
| age | File encryption | Recommended | GPG |
| Twingate / NetBird | Zero-trust access / WireGuard mesh | Praised (Twingate is a sponsor) | Port-forwarded VPN |

```bash
dotenvx encrypt                       # encrypts .env, writes .env.keys
echo ".env.keys" >> .gitignore && echo ".env.keys" >> .dockerignore
dotenvx run -- node server.js         # decrypts at runtime
gitleaks detect                       # scan history; --no-git for plain dirs
trivy image myapp:1.2.3               # CVEs in image; trivy fs . for lockfiles
```

Rewritten history can still hold secrets in dangling objects; rotate leaked keys rather than relying on history rewrites.

## Observability and serving

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| [Dozzle](https://github.com/amir20/dozzle) | Live Docker/K8s logs (`DOZZLE_MODE=k8s` needs get/list/watch pods) | Adopted on every cluster | ELK, CloudWatch for small setups |
| Caddy | Auto-HTTPS server (`reverse_proxy`) | "The goat" | Nginx + Certbot |
| Angie | Nginx fork, free dashboard/ACME/HTTP3 | Drop-in | Nginx Plus |
| Go pprof | Heap profiles (`go tool pprof -http=:8080`) | Find leaks, don't restart | Restart loops |
| Termshark | tshark TUI | Excellent | Wireshark GUI |

## Data stores

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| PostgreSQL + BM25/TimescaleDB/pgvector | General plus search, time series, vectors | "Toyota of databases" | Elasticsearch, InfluxDB |
| SQLite (`PRAGMA journal_mode=WAL`) | Embedded SQL | Right for most apps | Postgres for small apps |
| Neon / pg_dump+pg_restore copy | Branch DB before risky migrations | Recommended | Migrating prod directly |
| Valkey | Redis fork | Drop-in, adopted | Redis |
| RabbitMQ | Queues | Prefer over sync HTTP chains | HTTP fan-out |

## Self-hosting

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| Kamal | Zero-downtime Docker deploys over SSH | Brilliant | Kubernetes, PaaS |
| Dokploy / Coolify | Self-hosted PaaS | 4.5/5 and 4/5 | Vercel, Heroku |
| RustFS / Garage | S3-compatible storage | Top picks (removes egress) | MinIO, S3 |
| Restic | Encrypted dedup backups | Recommended | — |
| Pangolin | Self-hosted tunnel with SSO | Homelab favorite | Cloudflare Tunnel |
| Headscale | Self-hosted Tailscale control | Full control | Tailscale SaaS |

## CLI utilities

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| ripgrep, fd, bat, eza, sd | Search and core utils | Best in class / daily | grep, find, cat, ls, sed |
| jq + jqp | JSON | Core | — |
| xh (`--curl`) | HTTP testing | Daily driver | curl for manual tests |
| Yazi | Terminal file manager | Daily | ranger, Finder |
| Television (tv) | Channel-based fuzzy finder | Replaced 7 CLIs | kubectx pickers, log browsers |
| GNU Stow | Dotfile symlinks | Preferred | Nix Home Manager |

## AI coding agents

| Tool | Use for | Verdict | Replaces |
|---|---|---|---|
| Pi (pi.dev) | Minimal model-agnostic terminal agent | Creator's daily driver (runs without approvals by default: sandbox it) | OpenCode, Cursor |
| OpenCode | OSS agent, plan/build modes | Highly praised | Cursor |
| Goose | MCP-first Rust agent | Good, no model lock-in | Closed agents |
| Gemini CLI | Gemini agent | Fine for frontend, weak for DevOps | — |
| OpenSpec / Babysitter | Spec workflow / quality gates | Recommended against vibe coding | Unstructured loops |

## Default picks for agents

- Local AWS testing: Floci on `localhost:4566` before any real account.
- IaC: OpenTofu or Terraform, saved-plan apply, remote locked state.
- Containers: Podman or Docker with slim/distroless, digest-pinned, `.dockerignore`; inspect with LazyDocker.
- Kubernetes: k3d locally; k9s + stern + kubectx for inspection; Traefik ingress.
- Secrets: dotenvx for `.env`, Infisical for shared secrets, JIT creds via Teleport.
- Gates: Gitleaks + Trivy run by the agent before push (deep-mode has no CI); PR-Agent via the **pr-agent** technique for review.
- Git: LazyGit or CLI with worktrees (`wt`), rebase + `--force-with-lease`.
- Logs: Dozzle; serving: Caddy.
- Data: Postgres or SQLite (WAL); Valkey for cache.
- Deploy small apps: Compose on a VPS or Kamal before Kubernetes.

## Do / Avoid

**Do**
- Show the Terraform plan, then apply only `tfplan`.
- Point SDKs and providers at Floci with `skip_credentials_validation = true` for tests.
- Copy lockfiles before source, use `npm ci`, run as non-root, pin by digest.
- Debug with `docker diff`, `docker cp`, logs, k9s, stern.
- Run Gitleaks and Trivy before push or release; encrypt `.env` with dotenvx.
- Verify RBAC with `kubectl auth can-i ... --as=`.
- Work in a separate worktree; rebase; `--force-with-lease`.
- Branch the database (Neon or dump/restore) before risky migrations.
- Run autonomous agents in containers, Lima VMs, or worktrees with short-lived credentials.

**Avoid**
- Blindly applying AI-generated HCL; local state in production.
- Alpine for native deps; `latest` tags; missing `.dockerignore`.
- Plaintext `.env`, secrets baked into images or scripts, static keys in agent configs.
- S3 → Lambda → same-bucket write loops.
- Kubernetes by default when Compose, Swarm, or Kamal fits.
- Merge-button merge commits; plain `--force`.
- Expecting `docker update` to raise memory on a running container.
- Unsandboxed, approval-free agent runs.
- Treating these verdicts as vendor facts or benchmarks; check official docs for exact flags.

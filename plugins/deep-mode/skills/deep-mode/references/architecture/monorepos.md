# Organizing a Monorepo (2026)

Summary (facts checked 2026-11-11):
- A monorepo pays off only when code is shared across deployables AND you invest in affected-only CI plus caching; without that it is slower than a polyrepo ([Vercel](https://vercel.com/i/monorepos-full-stack-teams), [Google CACM](https://cacm.acm.org/research/why-google-stores-billions-of-lines-of-code-in-a-single-repository/fulltext)).
- Default JS/TS stack: pnpm workspaces + catalogs, `apps/` + `packages/`, Turborepo for task caching, Changesets only if you publish. Python: uv workspaces. Go: one `go.mod`. Rust: Cargo workspace. Polyglot at scale: Bazel 9 (Bzlmod only), Pants, or moon.
- Enforce package boundaries with a tool (Nx module boundaries, `turbo boundaries`, dependency-cruiser, sheriff, import-linter); agents do not respect conventions that are not checked.
- Agent context: one root `AGENTS.md` plus short per-package files. Harnesses load nested files differently (Codex: root to cwd only; Claude Code: subdirectories on demand; omp: ancestors plus pointers), so put package commands where the agent will actually start.
- Remote cache security is real: Nx deprecated its bucket cache plugins over cache poisoning (CVE-2025-36852); never let untrusted PR builds write to the cache `main` reads.

## 1. Monorepo or polyrepo

Primary write-ups:
- Google: benefits are unified versioning, code sharing, atomic changes, large-scale refactoring, visibility; costs are tooling investment, codebase complexity "including unnecessary dependencies and difficulties with code discovery", and code-health effort ([CACM 2016](https://cacm.acm.org/research/why-google-stores-billions-of-lines-of-code-in-a-single-repository/fulltext)). "A monolithic codebase in no way implies monolithic software design" (same source).
- Meta: one large monorepo on Sapling, built to serve tens of millions of files and commits ([Meta Engineering 2022](https://engineering.fb.com/2022/11/15/developer-tools/sapling-source-control-scalable)); branching inside it solved with full-repo and directory branching ([Meta 2025](https://engineering.fb.com/2025/10/16/developer-tools/branching-in-a-sapling-monorepo)).
- Uber: moved Go services from many small repos into a Go monorepo in 2018 with Bazel + Gazelle, affected-target hashing, and SubmitQueue to keep main green ([Uber Blog](https://www.uber.com/blog/go-monorepo-bazel/)).
- Shopify: in 2024 chose "one repository for all things Shopify ships" (World) plus Nix; CI had to scale "by an order of magnitude", merge queues "became load-bearing", the build cache "became a product"; payoff was an agent at repo root that can navigate cross-zone, with `AGENTS.md` files and skills in the repo ([Shopify Engineering 2026](https://shopify.engineering/under-the-river)).
- Vercel: a monorepo without incremental builds and shared cache "is strictly worse than a polyrepo"; polyglot stacks and single-app repos are signals against ([Vercel 2026](https://vercel.com/i/monorepos-full-stack-teams)).
- AWS CDK: start with one app per repo; move shared packages to their own repo when they serve several apps on independent cadences or different teams need access control ([AWS CDK best practices](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html)).

| Situation | Pick | Why | Source |
|---|---|---|---|
| One deployable, no shared code | Single-package repo (no workspace tooling) | No coordination cost to remove | [Vercel](https://vercel.com/i/monorepos-full-stack-teams) |
| Web + API + shared types/UI, 1-15 devs, TS | Monorepo: pnpm workspaces + Turborepo | Atomic cross-package changes; cheap setup; free remote cache | [Turborepo](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository) |
| TS frontend + Python or Go backend, small team | Monorepo, each language uses its native workspace; one task runner on top (Turborepo experimental uv/Go, or moon) | Shared API contracts change atomically; native tools stay the source of truth | [Turborepo Python](https://turborepo.dev/docs/guides/tools/python), [moon](https://moonrepo.dev/docs/setup-toolchain) |
| Many languages, 50+ engineers, hermetic builds needed | Bazel 9 (or Pants for Python/Go/JVM) | Fine-grained, cached, remote-executable graph | [Bazel 9](https://blog.bazel.build/2026/01/20/bazel-9.html), [Pants](https://www.pantsbuild.org/stable/docs/introduction/welcome-to-pants) |
| Library consumed by external users on its own cadence | Separate repo or publishable package with Changesets | Independent lifecycle and versioning | [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html), [Changesets](https://github.com/changesets/changesets) |
| Different orgs/teams need hard access control | Separate repos | Repo is the unit of access control on most hosts | [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html) |

## 2. Layout conventions

Turborepo recommends "splitting your packages into `apps/` for applications and services and `packages/` for everything else, like libraries and tooling"; it does not support nested packages (`apps/a` and `apps/a/b`), but you can group with `packages/group/*` if `packages/group` has no `package.json` ([Turborepo structure](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository)). Nx uses the same `apps`/`libs`-style split with tags ([Nx project dependency rules](https://nx.dev/docs/concepts/decisions/project-dependency-rules)).

```text
repo/
  AGENTS.md                 # repo-wide rules, commands, map of packages (keep short)
  CLAUDE.md                 # optional: "@AGENTS.md" + Claude-only notes (no symlink on Windows)
  .github/CODEOWNERS        # ownership; owner for CODEOWNERS itself
  .github/workflows/        # CI: affected-only, merge_group trigger
  apps/
    web/                    # deployable; own package.json, AGENTS.md, tests
    api/                    # deployable; owns its DB migrations if it is the only writer
  packages/
    ui/                     # internal package, @repo/ui, just-in-time TS
    domain/                 # shared types, schemas (zod/pydantic), no I/O
    db/                     # only if several apps share one database: schema + migrations + client
    typescript-config/      # @repo/typescript-config: base.json, nextjs.json, library.json
    eslint-config/          # or a root biome.json with nested "extends": "//"
  tools/                    # generators, codemods, repo scripts (not shipped)
  infra/                    # IaC shared across apps (network, DNS, accounts); per-app infra lives with the app
  docs/adr/0001-record-architecture-decisions.md
  package.json  pnpm-workspace.yaml  turbo.json  pnpm-lock.yaml
  pyproject.toml  uv.lock   # uv workspace root if Python members exist
```

Rules:
- Name internal packages under one scope (`@repo/*` in Turborepo examples) and depend on them with `workspace:*` ([Turborepo internal packages](https://turborepo.dev/docs/core-concepts/internal-packages)).
- Shared config is a package, not a root file every package reaches into: `@repo/typescript-config` with `base.json` extended by each `tsconfig.json` ([Turborepo TypeScript](https://turborepo.dev/docs/guides/tools/typescript)). Biome v2 supports a root `biome.json` with nested configs using `"extends": "//"` ([Biome big projects](https://biomejs.dev/guides/big-projects/)).
- DB schema and migrations: exactly one package owns each database's migrations. Shared DB: a `packages/database` package (`@repo/db`) owns schema, migrations directory, and client, and apps import it ([Prisma + Turborepo guide](https://www.prisma.io/docs/guides/deployment/turborepo)). Single-writer DB: keep migrations inside that app [inference].
- IaC: keep app-specific infrastructure next to the runtime code it deploys; AWS calls combining them "a best practice" ([AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html)). Shared foundation (network, DNS, org accounts) goes in `infra/` with its own pipeline [inference].
- ADRs: Nygard's original convention is in-repo, numbered sequentially, never reused, superseded rather than deleted ([Nygard 2011](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)). Use `docs/adr/`; package-local decisions may live in `<pkg>/docs/adr/` [inference].
- `tools/` vs `scripts/`: pick one name; nothing in it is imported by `apps/` [inference].
- CODEOWNERS: last matching pattern wins; any one listed owner's approval satisfies the requirement; give `/.github/CODEOWNERS` itself an owner ([GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)).

### Internal package strategies (TS)

| Strategy | When | Trade-off | Source |
|---|---|---|---|
| Just-in-time (export `.ts` from `exports`, no build) | Consumers use a bundler or TS-native runtime; small repo | No build cache for the package; cannot use TS `paths`; dependents see its type errors | [Turborepo](https://turborepo.dev/docs/core-concepts/internal-packages) |
| Compiled (`tsc` to `dist/`, `types` points at source) | Consumed by Node without bundler, or build time matters | More config; cacheable outputs | [Turborepo](https://turborepo.dev/docs/core-concepts/internal-packages) |
| Publishable | Ships to npm | Most config; use Changesets | [Turborepo](https://turborepo.dev/docs/core-concepts/internal-packages) |

Use Node subpath imports (`"imports": {"#*": "./src/*"}`) instead of `compilerOptions.paths` inside packages ([Turborepo TypeScript](https://turborepo.dev/docs/guides/tools/typescript)).
TypeScript project references: Turborepo says "You likely don't need" them (extra config and caching layer) ([Turborepo TypeScript](https://turborepo.dev/docs/guides/tools/typescript)); Nx recommends workspaces + project references and auto-syncs them with `nx sync` ([Nx TS project linking](https://nx.dev/docs/concepts/typescript-project-linking)). Pick per tool, not both philosophies.
TypeScript 7.0 (Go port, released 2026-07) keeps `--build` and adds `--builders` for parallel project builds ([TS 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)).

## 3. Enforced boundaries

| Tool | What | License / terms | Latest release | Agent notes | Source |
|---|---|---|---|---|---|
| Nx `@nx/enforce-module-boundaries` | ESLint rule: tag projects (`scope:*`, `type:*`), `depConstraints` allow lists | MIT | Nx 24.0.6, 2026-11-10 | Strongest TS option; needs Nx project graph | [Nx](https://nx.dev/docs/features/enforce-module-boundaries) |
| `turbo boundaries` | Flags imports outside package dir and undeclared deps; tag allow/deny rules, transitive | MIT; experimental | turbo 2.11.11, 2026-11-11 | Run in CI; catches `../../packages/x/src` imports | [Turborepo](https://turborepo.dev/docs/reference/boundaries) |
| dependency-cruiser | Rule-based `forbidden` graph checks, cycles, orphans, missing deps | MIT | v18.7.2, 2026-11-02 | Tool-agnostic; `depcruise --init` writes sane defaults | [README](https://github.com/sverweij/dependency-cruiser) |
| Sheriff | TS module boundaries via `index.ts` public APIs + tag rules | MIT | v0.20.0, 2026-10-07 (pre-1.0) | Good inside one large app package | [README](https://github.com/softarc-consulting/sheriff) |
| import-linter | Python contracts: forbidden, protected, layers, independence, acyclic siblings | BSD-2-Clause | v2.16, 2026-11-06 | Required for uv workspaces: uv "can't ensure that packages don't import dependencies declared by another workspace member" | [docs](https://import-linter.readthedocs.io/en/stable/), [uv](https://docs.astral.sh/uv/concepts/projects/workspaces/) |
| Go `internal/` | Compiler-enforced package privacy | BSD-3 (Go) | Go 1.27.4 | Free boundary; use it before inventing modules | [Go modules wiki](https://go.dev/wiki/Modules) |

Nx example:
```js
'@nx/enforce-module-boundaries': ['error', { depConstraints: [
  { sourceTag: 'type:app', onlyDependOnLibsWithTags: ['type:feature', 'type:ui', 'type:domain'] },
  { sourceTag: 'type:domain', onlyDependOnLibsWithTags: ['type:domain'] } ] }]
```

## 4. JS/TS tooling

| Tool | What | License / free terms | Latest release | Agent notes | Source |
|---|---|---|---|---|---|
| pnpm workspaces + catalogs | Strict node_modules; `workspace:` protocol; `catalog:` pins one version in `pnpm-workspace.yaml` | MIT | v12.18.0, 2026-11-05 | Use `catalogMode: strict` to stop agents adding stray versions; `catalog:` is rewritten on publish | [pnpm catalogs](https://pnpm.io/catalogs) |
| npm / Yarn 4 / Bun workspaces | `workspaces` globs in root package.json | npm Artistic-2.0; Yarn BSD-2; Bun MIT | Yarn 4.18.1 2026-09-24; Bun 1.4.4 2026-10-22 | Fine for small repos; pnpm catches phantom deps better [inference] | [Turborepo structure](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository) |
| Turborepo | Task graph, local + remote cache, `--affected`, `boundaries`, `prune` for Docker | MIT. Vercel Remote Cache "free to use on all plans"; self-host via OpenAPI spec | 2.11.11, 2026-11-11 | Experimental uv, Go, Cargo support; can keep a managed block in root `AGENTS.md`; shares local cache across worktrees | [Remote caching](https://turborepo.dev/docs/core-concepts/remote-caching), [AI guide](https://turborepo.dev/docs/guides/ai) |
| Nx | Project graph, affected, generators, module boundaries, `nx sync` for TS refs | MIT core. Nx Cloud: Hobby free (50K credits/mo), Team from $29/mo (paid) | 24.0.6, 2026-11-10 | Bucket cache plugins `@nx/s3-cache` etc. deprecated 2026-05-21; `nx configure-ai-agents` writes AGENTS.md/skills | [Nx pricing](https://nx.dev/pricing), [deprecation](https://nx.dev/docs/reference/deprecated/self-hosted-cache-packages), [AI setup](https://nx.dev/docs/getting-started/ai-setup) |
| moon | Rust task runner, polyglot toolchains (Node, Bun, Deno, Go, Python, Rust, PHP, Ruby) via proto | MIT | v2.6.5, 2026-10-29 (v2.0 Feb 2026; v1 docs frozen) | Good polyglot middle ground; v1 configs in training data are stale | [moon v2](https://moonrepo.dev/blog/moon-v2.0), [toolchains](https://moonrepo.dev/docs/setup-toolchain) |
| Rush | Microsoft's large-repo manager (pnpm-based, publishing, policies) | MIT | 5.182.1, 2026-10-30 | Heavy; pick only for many published packages and strict policies [inference] | [npm @microsoft/rush](https://www.npmjs.com/package/@microsoft/rush) |
| Lerna | Versioning/publishing; task running delegates to Nx | MIT; Nx took over stewardship in 2022 | v10.1.2, 2026-11-06 | Maintained, not dead; new repos usually use Changesets or `nx release` | [Lerna and Nx](https://lerna.js.org/docs/lerna-and-nx) |
| Changesets | Per-PR intent files, then `changeset version` / `publish` | MIT | @changesets/cli 3.0.3, 2026-09-14 | Only needed if you publish or version packages | [Changesets](https://github.com/changesets/changesets) |

Root `package.json` scripts delegate to the runner (`"build": "turbo run build"`), and each package defines its own `build`, `lint`, `test`, `check-types` ([Turborepo structure](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository)).

## 5. Python, Go, Rust, polyglot

| Ecosystem | Pick | Key facts | Latest | Source |
|---|---|---|---|---|
| Python | uv workspace | One `uv.lock` for all members; `uv run --package <m>`; member deps via `{ workspace = true }`; one `requires-python` (intersection); not for members with conflicting requirements, use path deps instead | uv 0.13.7, 2026-11-03 (Apache-2.0/MIT) | [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/) |
| Python (legacy) | Poetry only per-project | No native workspaces; monorepo issue #936 closed "not planned"; plugins exist | Poetry 2.5.1, 2026-09-20 | [issue #936](https://github.com/python-poetry/poetry/issues/936) |
| Python at scale | Pants | Dependency inference by static analysis, fine-grained invalidation, remote cache; Python, Go, Java, Scala, Kotlin, Shell, Docker | 2.32.2, 2026-11-01 (Apache-2.0) | [Pants](https://www.pantsbuild.org/stable/docs/introduction/welcome-to-pants) |
| Go | One `go.mod` at the Go root | Multi-module repos take "more work on an on-going basis"; `go.work` for local multi-module dev, and committing it is "generally inadvisable" | Go 1.27.4 | [Go wiki](https://go.dev/wiki/Modules), [go.dev/ref/mod](https://go.dev/ref/mod) |
| Rust | Cargo workspace | Shared `Cargo.lock`; `[workspace.dependencies]` for inherited versions; virtual manifests must set `resolver` | stable toolchain | [Cargo workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html) |
| Polyglot, large | Bazel 9 | 9.0 (Jan 2026) removed WORKSPACE entirely; Bzlmod `MODULE.bazel` only; language rules now external (e.g. `rules_cc`) | 9.3.2, 2026-11-05 (Apache-2.0) | [Bazel 9 LTS](https://blog.bazel.build/2026/01/20/bazel-9.html) |
| Polyglot, Meta-style | Buck2 | No stable release tag; bi-monthly date tags (latest 2026-11-01) | Apache-2.0 | [Buck2 README](https://github.com/facebook/buck2) |

## 6. CI for monorepos

| Need | Do | Source |
|---|---|---|
| Run only what changed | `turbo run build lint test --affected` (defaults to `main...HEAD`; override with `TURBO_SCM_BASE`) or `nx affected -t lint test build` with `nrwl/nx-set-shas` | [turbo run](https://turborepo.dev/docs/reference/run), [Nx affected](https://nx.dev/docs/features/ci-features/affected) |
| Git history for affected | `actions/checkout` with `fetch-depth: 0` and `filter: blob:none` (blobless, full history) | [Turborepo](https://turborepo.dev/docs/reference/run), [actions/checkout](https://github.com/actions/checkout) |
| Path-based workflow triggers | Do not mark path-filtered workflows as required: skipped workflows stay "Pending" and block merge. Use job-level conditions (skipped jobs report Success) or an always-run gate job with `needs` + `always()` | [GitHub required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks) |
| Job-level change detection | `dorny/paths-filter` (MIT, v4.0.3 2026-08-05) outputs per-path booleans for `if:` | [paths-filter](https://github.com/dorny/paths-filter) |
| Busy main branch | GitHub merge queue; workflows must also trigger `on: merge_group` or checks never report | [Merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) |
| Remote cache safety | Signed artifacts (`remoteCache.signature: true` + `TURBO_REMOTE_CACHE_SIGNATURE_KEY`); a custom Nx cache server must return 409 on existing keys; give PR builds read-only cache tokens [inference for Turborepo] | [Turborepo](https://turborepo.dev/docs/core-concepts/remote-caching), [Nx CREEP notice](https://nx.dev/docs/reference/deprecated/self-hosted-cache-packages) |
| Docker images per app | `turbo prune <app> --docker` produces a pruned workspace for the image build | [turbo prune](https://turborepo.dev/docs/reference/prune) |

Big-repo git (only when clone/status is slow): `git sparse-checkout set <dirs>` with cone mode and sparse index ([GitHub blog](https://github.blog/open-source/git/make-your-monorepo-feel-small-with-gits-sparse-index)); partial clone `--filter=blob:none` ([git partial clone](https://git-scm.com/docs/partial-clone)); `scalar clone` (in Git since 2.38) turns on sparse-checkout, background maintenance, commit-graph, multi-pack-index ([git scalar](https://git-scm.com/docs/scalar), [Story of Scalar](https://github.blog/open-source/git/the-story-of-scalar/)). The standalone `microsoft/scalar` repo's last release is 2021; use the Git-bundled one.

```yaml
on: { pull_request: {}, merge_group: {} }
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7   # latest major as of 2026-11 (v7.0.1)
        with: { fetch-depth: 0, filter: blob:none }
      - uses: pnpm/action-setup@v6  # latest major as of 2026-11 (v6.1.1)
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo run lint check-types test build --affected
```

## 7. Agent-friendliness

How harnesses discover nested instruction files:

| Harness | Loads at start | Below cwd | Gotchas | Source |
|---|---|---|---|---|
| AGENTS.md convention | Root file; nested per package | "The closest AGENTS.md to the edited file wins" | Behavior is per harness, not guaranteed | [agents.md](https://agents.md/) |
| Codex | Global `~/.codex/AGENTS.md`, then project root down to cwd; per dir `AGENTS.override.md` > `AGENTS.md` > fallbacks; concatenated root first | Not loaded: Codex "stops searching once it reaches your current directory" | 32 KiB combined cap (`project_doc_max_bytes`); start Codex in the package dir for package rules | [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md) |
| Claude Code | `CLAUDE.md`/`CLAUDE.local.md` in cwd and every ancestor | Subdirectory `CLAUDE.md` loads when Claude reads/edits a file there | Reads `AGENTS.md` (v2.1.277+) only if no `CLAUDE.md`/`CLAUDE.local.md` on the path; target under 200 lines; on Windows use `@AGENTS.md` import, not a symlink | [Claude memory](https://code.claude.com/docs/en/memory), [large codebases](https://code.claude.com/docs/en/large-codebases) |
| omp | Standalone `AGENTS.md`/`CLAUDE.md` from cwd up to repo root, one per depth, all depths kept, closer files last | With workspace tree on, deeper `AGENTS.md` files are listed as pointers in `<dir-context>`, not injected | Task subagents drop files named `AGENTS.md`; put must-follow rules in `.omp/RULES.md` | [omp context files](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md) |

Rules:
- Root `AGENTS.md`: what the repo is, package map (one line per package), the exact commands (`pnpm turbo run test --filter=<pkg>`), boundaries rules, where ADRs/migrations/infra live. Keep it under ~200 lines ([Claude memory](https://code.claude.com/docs/en/memory)).
- Package `AGENTS.md`: stack, local commands runnable from the package dir, invariants ("never edit a merged migration"). Claude's own monorepo example uses exactly this split ([Claude large codebases](https://code.claude.com/docs/en/large-codebases)).
- Make every package testable in isolation: own `test`, `lint`, `check-types` scripts; `turbo run test --filter=<pkg>` or `uv run --package <m> pytest` works without building unrelated apps.
- One instruction file per directory for all tools: `AGENTS.md`, with `CLAUDE.md` containing `@AGENTS.md` only where Claude-specific notes exist ([Claude memory](https://code.claude.com/docs/en/memory)).
- Codebase maps: prefer the tool's graph over prose. `turbo ls` / `turbo query` ([Turborepo reference](https://turborepo.dev/llms.txt)), `nx show projects` / `nx graph` ([Nx AI](https://nx.dev/docs/features/enhance-ai)), Aider-style repo maps rank files by dependency graph to fit a token budget ([Aider repo map](https://aider.chat/docs/repomap.html)). Keep the package map in root `AGENTS.md` to one line each so it does not rot.
- Parallel agents: one git worktree per agent. Claude Code `--worktree` creates `.claude/worktrees/<name>`; copy gitignored `.env` via `.worktreeinclude`; `worktree.sparsePaths` checks out only listed packages; `symlinkDirectories: ["node_modules"]` avoids reinstalling ([Claude worktrees](https://code.claude.com/docs/en/worktrees), [large codebases](https://code.claude.com/docs/en/large-codebases)). Codex app worktrees also honor `.worktreeinclude` and keep the latest 15 by default ([Codex worktrees](https://developers.openai.com/codex/app/worktrees)). Turborepo shares the local cache across worktrees ([Turborepo AI](https://turborepo.dev/docs/guides/ai)).
- Each worktree is a fresh checkout: run install there, and give each dev server its own port [inference].

## 8. Decision table: situation -> layout/tool

| Situation | Layout | Tooling | Why | Source |
|---|---|---|---|---|
| Solo dev, Next.js + API in TS | `apps/web`, `apps/api`, `packages/{ui,domain,typescript-config}` | pnpm + catalogs, Turborepo, JIT packages | Lowest config, free Vercel remote cache | [Turborepo](https://turborepo.dev/docs/core-concepts/internal-packages) |
| TS web + Python API | `apps/web`, `apps/api` (Python), root `pyproject.toml` uv workspace | pnpm + uv; Turborepo `experimentalPythonWorkspaces` or plain package scripts | Native lockfiles stay authoritative; Turborepo uv support is experimental | [Turborepo Python](https://turborepo.dev/docs/guides/tools/python) |
| Go services + TS frontend | `services/*` under one `go.mod`, `apps/web` | Go toolchain + Turborepo (Go experimental) or moon | Single Go module avoids multi-module versioning | [Go wiki](https://go.dev/wiki/Modules), [moon](https://moonrepo.dev/docs/setup-toolchain) |
| Angular or many TS libs, want generators and strict boundaries | `apps/`, `libs/` with `scope:`/`type:` tags | Nx (+ Nx Cloud Hobby if desired) | Module-boundary rule, `nx sync` | [Nx](https://nx.dev/docs/features/enforce-module-boundaries) |
| Publishing several npm packages | `packages/*` publishable | pnpm + Changesets (or `nx release`) | Versioning per PR intent | [Changesets](https://github.com/changesets/changesets) |
| Python-only, several services sharing libs | `apps/*`, `libs/*` uv workspace | uv + import-linter (+ Pants when CI is slow) | uv cannot enforce member imports | [uv](https://docs.astral.sh/uv/concepts/projects/workspaces/) |
| Hermetic multi-language at org scale | `//services`, `//libs`, BUILD files | Bazel 9 + remote cache/exec | Only Bzlmod supported now | [Bazel 9](https://blog.bazel.build/2026/01/20/bazel-9.html) |

## Traps for agents

- Assuming a nested `AGENTS.md` is in context. Codex never loads files below cwd; Claude loads them only after touching a file there; omp lists them as pointers. Read the package `AGENTS.md` before editing a package ([Codex](https://developers.openai.com/codex/guides/agents-md), [Claude](https://code.claude.com/docs/en/memory), [omp](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md)).
- Adding a `CLAUDE.md` or `CLAUDE.local.md` next to an `AGENTS.md`: Claude Code then stops reading `AGENTS.md` by default ([Claude memory](https://code.claude.com/docs/en/memory)).
- Symlinking `CLAUDE.md` to `AGENTS.md` in a repo cloned on Windows: Git checks it out as a one-line text file unless `core.symlinks` is on ([Claude memory](https://code.claude.com/docs/en/memory)).
- Linking packages with TS `paths` or relative `../../packages/x/src` imports instead of `workspace:*` deps; JIT packages break and `turbo boundaries` flags it ([Turborepo TS](https://turborepo.dev/docs/guides/tools/typescript), [boundaries](https://turborepo.dev/docs/reference/boundaries)).
- Importing a dependency a package does not declare (hoisting hides it); in uv workspaces nothing stops it, so add import-linter ([uv](https://docs.astral.sh/uv/concepts/projects/workspaces/)).
- Installing a dependency at the root or with a different version per package instead of the catalog ([pnpm catalogs](https://pnpm.io/catalogs)).
- Mixing philosophies: adding TS project references to a Turborepo repo that its docs advise against, or hand-editing references Nx syncs ([Turborepo TS](https://turborepo.dev/docs/guides/tools/typescript), [Nx](https://nx.dev/docs/concepts/typescript-project-linking)).
- Nesting packages (`apps/a/b`) under Turborepo: unsupported ([Turborepo structure](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository)).
- Requiring a path-filtered workflow in branch protection; or enabling a merge queue without `merge_group` ([GitHub checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks), [merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)).
- `fetch-depth: 1` (the checkout default) with `--affected` or `nx affected`: no base to diff ([Nx affected](https://nx.dev/docs/features/ci-features/affected)).
- Suggesting stale tooling from training data: Nx `tasksRunnerOptions` or `@nx/s3-cache` (deprecated, CVE-2025-36852), Bazel `WORKSPACE` (removed in 9.0), moon v1 configs, standalone `microsoft/scalar` ([Nx](https://nx.dev/docs/reference/deprecated/self-hosted-cache-packages), [Bazel](https://blog.bazel.build/2026/01/20/bazel-9.html)).
- Declaring Lerna dead and migrating away for no reason; it is maintained by the Nx team ([Lerna](https://lerna.js.org/docs/lerna-and-nx)).
- Committing `go.work` ([go.dev/ref/mod](https://go.dev/ref/mod)); creating a `go.mod` per service by default ([Go wiki](https://go.dev/wiki/Modules)).
- Creating a package per idea. Google names "unnecessary dependencies" as a core monorepo cost; split when there is a second consumer or a separate deploy [inference from [CACM](https://cacm.acm.org/research/why-google-stores-billions-of-lines-of-code-in-a-single-repository/fulltext)].
- Two packages writing migrations for the same database; migrations must have one owner ([Prisma guide](https://www.prisma.io/docs/guides/deployment/turborepo)).
- Running parallel agents in one checkout instead of worktrees; or forgetting install and `.env` in a new worktree ([Claude worktrees](https://code.claude.com/docs/en/worktrees)).
- Running root-wide `build`/`test` to verify a one-package change; use `--filter=<pkg>` or `--affected` [inference].

## Default for a solo dev / small team

1. One repo. pnpm workspaces with `catalog:` (`catalogMode: strict`), `apps/*` + `packages/*`, scope `@repo/*`, internal packages just-in-time until build time hurts ([pnpm](https://pnpm.io/catalogs), [Turborepo](https://turborepo.dev/docs/core-concepts/internal-packages)).
2. Turborepo for `build`/`lint`/`check-types`/`test`; Vercel Remote Cache (free) or none; turn on `remoteCache.signature` if remote cache is used ([Turborepo](https://turborepo.dev/docs/core-concepts/remote-caching)).
3. Python members in a root uv workspace; Go in one module; Rust in one Cargo workspace. Do not adopt Bazel/Pants until CI time is the bottleneck ([uv](https://docs.astral.sh/uv/concepts/projects/workspaces/), [Go](https://go.dev/wiki/Modules)).
4. Boundaries in CI from day one: `turbo boundaries` (or dependency-cruiser) for TS, import-linter for Python, `internal/` for Go.
5. Shared config packages (`@repo/typescript-config`, root `biome.json` + nested `"extends": "//"`); DB schema and migrations in exactly one package; app infra next to the app, shared infra in `infra/`; ADRs in `docs/adr/`.
6. CI: `--affected` with `fetch-depth: 0` + `filter: blob:none`, one always-run required gate job, `merge_group` trigger once a merge queue is on.
7. Root `AGENTS.md` under ~200 lines with package map and commands; a short `AGENTS.md` per app; `CLAUDE.md` = `@AGENTS.md` only if needed; `.worktreeinclude` for `.env`; one worktree per parallel agent.
8. Add Changesets only when something is published; add CODEOWNERS when a second person owns a package.

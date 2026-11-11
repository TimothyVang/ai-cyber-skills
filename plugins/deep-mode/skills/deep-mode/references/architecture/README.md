# Architecture: monorepos, ontology, databases, backend infrastructure

Read before designing or changing a project's shape: repo layout and workspace tooling, the domain vocabulary and data model, the database and its migrations, or the backend services, jobs, APIs, observability, and deployment. Researched 2026-11-11 from primary sources (official docs, specs, vendor pricing and engineering blogs, GitHub releases and licenses). Each claim carries its link; `[inference]` and `[unverified]` mean what they say. Versions, licenses, and free tiers move: recheck the one you pick.

| File | Read when |
|---|---|
| `monorepos.md` | Monorepo or not; `apps/` and `packages/` layout; pnpm, Turborepo, Nx, uv, Go, Cargo, Bazel; enforced boundaries; affected-only CI and caching; nested `AGENTS.md`; worktrees for parallel agents |
| `ontology.md` | Naming the domain: glossary, bounded contexts, ADRs; one typed model (Pydantic, Zod, LinkML) feeding API, DB, and agent tools; RDF, OWL, SHACL; property graphs; semantic layers; Palantir-style ontology for agent actions; GraphRAG and agent memory |
| `databases.md` | Choosing a database or extension, hosted free tiers and branching, schema and migrations in the repo, ORMs, zero-downtime migrations, tenancy and RLS, IDs, backups, and letting agents near a database safely |
| `backend-infrastructure.md` | Monolith or services, reliability (timeouts, retries, idempotency, SLOs, health checks), queues and durable workflows, caching, API style and errors, OpenTelemetry, deployment and IaC, capacity and cost |

These files build on `references/cloudxberry/backend-system-design.md` (API naming, indexing, cache and queue basics) and the `model-the-domain` principle. Where they disagree, these primary-source files win: for example, retries follow the AWS Builders' Library token-bucket advice rather than a circuit breaker on every call. Cloud security and pipelines stay in `references/cloud-devsecops/`; secrets and auth in `references/credentials/README.md`.

## Rules for the agent

1. **Name before you build.** Add or reuse terms in `docs/GLOSSARY.md` and map each to one code, DB, API, and event name. Record a choice between real options as an ADR in `docs/adr/`.
2. **One source of truth for the domain model.** A typed model (Pydantic or Zod; LinkML when three or more artifacts or languages need it) feeds the API schema, DB mapping, and agent tool schemas. Never hand-maintain two copies.
3. **Start simple and say what would force a change.** Modular monolith, one Postgres, a Postgres-backed job queue, REST plus OpenAPI. Add a service, queue, graph, or vector store only when you can name the force (scale, isolation, ownership, query shape) and write it in the ADR.
4. **One repo, enforced boundaries.** `apps/*` and `packages/*`; one package owns each database's schema and migrations; boundaries checked in CI (`turbo boundaries` or dependency-cruiser, import-linter, Go `internal/`).
5. **Migrations are expand-contract and reviewed.** Lint them (Squawk), set `lock_timeout`, build indexes concurrently, and never run destructive commands (`DROP`, `TRUNCATE`, `migrate reset`, `push --force`) against shared data without the user's yes.
6. **Agents get least-privilege data access.** Separate owner, app, and read-only agent roles; a branch database per PR or agent; no production credentials for agents. Read-only still leaks: prompt injection can exfiltrate what the role can read.
7. **Every remote call has a timeout; retry at one layer** with capped exponential backoff and jitter, and only idempotent operations (`Idempotency-Key` on creates and payments).
8. **Observe from day one.** OpenTelemetry traces and JSON logs with trace IDs, liveness that checks nothing external, readiness that does, and one availability and one latency SLO per user-facing API.
9. **Check the license and release date before adopting a tool.** BSL, SSPL, FSL, and AGPL each carry different obligations; archived or unmaintained tools are not defaults.
10. **Prove it on the real thing.** Tests run against a real database (Testcontainers or PGlite) with migrations applied, not mocks; load-test before launch.

## Default stack for a solo dev or small team

| Area | Default | Grows into |
|---|---|---|
| Repo | One repo: pnpm workspaces with catalogs, `apps/*` + `packages/*`, Turborepo with free Vercel Remote Cache; Python as a uv workspace, Go as one module | Nx when you want generators and a project graph; Bazel or Pants only when CI time is the bottleneck |
| Agent context | Root `AGENTS.md` under ~200 lines with the package map and commands; a short `AGENTS.md` per app; one worktree per parallel agent under `.worktrees/` | Per-package skills and verify skills |
| Domain | `docs/GLOSSARY.md`, ADRs, one Pydantic or Zod model; agents act through typed action tools, never raw write SQL | LinkML for multi-language models; Apache AGE on Postgres for graph traversal; Graphiti for agent memory |
| Database | Postgres 18 (Neon Free for branching, or Supabase Free with auth and storage); `packages/db` owns schema, migrations, seeds, client, and types | Paid plan with PITR before real users; pgvector, FTS, and pg_partman before separate stores |
| Data access | Drizzle (TS), SQLAlchemy 2 + Alembic (Python), sqlc + goose (Go); `uuidv7()` keys; `tenant_id` + RLS with `FORCE ROW LEVEL SECURITY` | db-per-tenant only for contractual isolation |
| Backend | One container, `web` and `worker` processes, modules by domain with a public `index` | Split a service only for a named force |
| Jobs and workflows | pg-boss or Graphile Worker (Node), River (Go), DBOS or pgmq (Python), enqueued in the business transaction | DBOS, Hatchet, or Temporal when flows run minutes or wait on humans |
| API | REST + OpenAPI 3.1, RFC 9457 errors, cursor pagination, idempotency keys | gRPC for internal service-to-service; tRPC only for a TS-only frontend |
| Observability | OpenTelemetry SDK and Collector to SigNoz self-hosted or a vendor free tier; Sentry free tier for errors | Grafana LGTM when you run your own stack |
| Deploy | Render, Railway, or Fly for zero ops, or Kamal or Coolify on one VPS; preview deploy per PR; OpenFeature-compatible flags | OpenTofu once there are cloud resources beyond the PaaS; Kubernetes only when a team operates it |

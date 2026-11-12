# Databases for agent-built apps (2026): choose, organize, migrate, operate safely

Facts checked 2026-11-11 against official docs, pricing pages, and GitHub/npm/PyPI release metadata. Version and price figures go stale; re-check before quoting.

- Default to **PostgreSQL 18** with extensions before adding another datastore. Postgres 14 reaches end of life on 2026-11-12, and Postgres 19 is at RC1 ([versioning](https://www.postgresql.org/support/versioning/)).
- Keep schema and migrations in the repo (`packages/db`). Commit the generated SQL, review it like code, and run migrations through expand-contract. Never run `push`/`reset` workflows against shared databases.
- Use one connection string per role: owner (migrations only), app (DML only), and agent (read-only with timeouts). Agents get a branch or a throwaway database, never production credentials ([Neon MCP guidance](https://neon.com/docs/ai/neon-mcp-server), [Replit incident response](https://replit.com/blog/introducing-a-safer-way-to-vibe-code-with-replit-databases)).
- A read-only MCP server still leaks data through prompt injection. Least privilege, project scoping, and human review are what actually limit damage ([Supabase](https://supabase.com/blog/defense-in-depth-mcp)).
- Test against a real Postgres (Testcontainers, PGlite, or a DB branch), not mocks or SQLite stand-ins ([Prisma AGENTS.md for databases](https://www.prisma.io/blog/agents-md-for-databases)).

## 1. Workload -> database

| Situation | Pick | Why | Source |
|---|---|---|---|
| New web/API app, relational data, any size a small team will see | Postgres 18 | 5-year support window per major; extensions cover vectors, geo, time series, partitioning | [versioning](https://www.postgresql.org/support/versioning/) |
| Single-server app, low/medium write traffic, embedded or local-first | SQLite (WAL) | SQLite says sites under ~100K hits/day work fine (a conservative estimate); one writer at a time | [whentouse](https://www.sqlite.org/whentouse.html) |
| Many clients over a network, write-heavy, multi-server | Client/server RDBMS (Postgres) | SQLite's own checklist says to pick client/server when the data is separated from the app by a network | [whentouse](https://www.sqlite.org/whentouse.html) |
| Database per agent/user/tenant at very large counts | Turso Cloud, Cloudflare D1, or Neon project-per-tenant | Free and paid tiers are built for many small DBs (D1 paid: 100,000 DBs included) | [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [Neon pricing](https://neon.com/pricing) |
| Local/batch analytics on Parquet/CSV, notebooks, CI reports | DuckDB (embedded) | In-process OLAP, MIT, v2.0.0 released 2026-10-21 | [duckdb releases](https://github.com/duckdb/duckdb/releases) |
| Shared cloud analytics on DuckDB | MotherDuck (paid beyond Lite) | Lite: $0, 10 GB storage, 10 h Pulse compute/month | [MotherDuck pricing](https://motherduck.com/product/pricing/) |
| High-volume event/log analytics (billions of rows, aggregations) | ClickHouse | Columnar OLAP, Apache-2.0, monthly stable plus LTS lines | [ClickHouse releases](https://github.com/ClickHouse/ClickHouse/releases) |
| Time series inside an existing Postgres | TimescaleDB extension | Apache-2.0 core plus Timescale License (TSL) features | [license](https://github.com/timescale/timescaledb/blob/main/LICENSE) |
| Embeddings for RAG next to app data | pgvector | HNSW/IVFFlat indexes, filtering, iterative index scans (0.8.0+) | [pgvector](https://github.com/pgvector/pgvector) |
| In-app search over your own tables | Postgres full-text search | Built in; no sync pipeline | [textsearch](https://www.postgresql.org/docs/current/textsearch.html) |
| Typo-tolerant instant search UX | Meilisearch or Typesense | Purpose-built engines; check the licenses below | [Meilisearch](https://github.com/meilisearch/meilisearch), [Typesense](https://github.com/typesense/typesense) |
| Cache, rate limits, ephemeral counters | Valkey (BSD) or Redis 8 (AGPLv3 option) | Licensing differs; see section 3 | [Valkey](https://github.com/valkey-io/valkey), [Redis AGPL](https://redis.io/blog/agplv3/) |
| Existing MySQL/Vitess shop | MySQL 8.4/9.7 line or PlanetScale (paid) | Stay on what the team runs; no reason to migrate a working system | [mysql-server tags](https://github.com/mysql/mysql-server/tags) |
| Document-shaped data, no need for joins/transactions across docs | Postgres `jsonb` first; MongoDB only if team expertise demands it | MongoDB Community is SSPL (not OSI) | [mongo LICENSE](https://github.com/mongodb/mongo/blob/master/LICENSE-Community.txt) |

Rules:
- Add a second datastore only after measuring that Postgres fails a concrete requirement. Every extra store adds a sync path, a backup plan, and a credential that agents can mishandle [inference].
- SQLite on a network filesystem risks corruption because of buggy file locking ([whentouse](https://www.sqlite.org/whentouse.html)). Never put it on NFS/SMB shares, including Windows mapped drives.

## 2. Engines and extensions (tool table)

| Tool | What | License / free terms | Latest release | Agent notes | Source |
|---|---|---|---|---|---|
| PostgreSQL | RDBMS | PostgreSQL License | 18.6 current; 19 RC1 2026-10-15 | `uuidv7()` built in from 18; 14 EOL 2026-11-12 | [versioning](https://www.postgresql.org/support/versioning/) |
| pgvector | Vector type + ANN indexes | PostgreSQL License | v0.8.7 (tag 2026-10-01) | HNSW: better speed/recall than IVFFlat, slower builds, more memory; `halfvec` to save space | [repo](https://github.com/pgvector/pgvector) |
| pgvectorscale | DiskANN-style index for pgvector | PostgreSQL License | 0.9.1 (2026-09-04) | Only when pgvector HNSW memory becomes the bottleneck | [repo](https://github.com/timescale/pgvectorscale) |
| PostGIS | Geospatial | GPL-2.0 | 3.6.4; 3.7.0rc3 | Offered by most managed Postgres (Neon lists it on every plan) | [tags](https://github.com/postgis/postgis/tags), [Neon](https://neon.com/pricing) |
| pg_partman | Partition management | PostgreSQL License | v5.5.0 (2026-07-22) | Use for append-heavy tables (events, logs) past tens of GB [inference] | [repo](https://github.com/pgpartman/pg_partman) |
| TimescaleDB | Time series | Apache-2.0 + TSL (`tsl/` dir) | 2.31.0 (2026-10-20) | TSL's main restriction is offering it as a DBaaS; `SHOW timescaledb.license` shows the edition | [TSL](https://www.timescale.com/legal/licenses), [editions](https://docs.tigerdata.com/about/latest/timescaledb-editions) |
| Citus | Distributed Postgres | AGPL-3.0 | v14.3.0 (2026-10-23) | Only for real sharding needs | [repo](https://github.com/citusdata/citus) |
| SQLite | Embedded RDBMS | Public domain | n/a | One writer at a time; WAL for concurrency | [whentouse](https://www.sqlite.org/whentouse.html) |
| Turso Database (ex-Limbo) | SQLite rewrite in Rust | MIT | v0.8.3 (2026-10-12), pre-1.0 | libSQL README calls it beta and says new projects should look at it; Turso joined Supabase 2026-10-02 | [turso](https://github.com/tursodatabase/turso), [libsql](https://github.com/tursodatabase/libsql), [news](https://turso.tech/blog/turso-is-joining-supabase) |
| libSQL | SQLite fork | MIT | server v0.24.32 (2025-02-14) | No server release in 12+ months; repo still pushed; feature work moved to Turso Database | [repo](https://github.com/tursodatabase/libsql) |
| Litestream | SQLite WAL streaming backup to object storage | Apache-2.0 | v0.5.18 (2026-11-03) | README status badge: beta | [repo](https://github.com/benbjohnson/litestream) |
| LiteFS | FUSE-replicated SQLite | Apache-2.0 | v0.5.14 (2025-04-22) | Beta; **no release in 12+ months**; avoid for new work | [repo](https://github.com/superfly/litefs) |
| DuckDB | Embedded OLAP | MIT | v2.0.0 (2026-10-21) | Node: `@duckdb/node-api` 2.0.0-r.1 | [repo](https://github.com/duckdb/duckdb) |
| ClickHouse | Columnar OLAP server | Apache-2.0 | v26.10.2 stable; v26.3 LTS | Prefer the LTS line for self-hosting | [releases](https://github.com/ClickHouse/ClickHouse/releases) |
| MySQL | RDBMS | GPL-2.0 (Community) | tags mysql-9.7.4, mysql-26.10.0, mysql-8.4.9 | Which line is LTS after 8.4: [unverified] | [tags](https://github.com/mysql/mysql-server/tags) |
| MongoDB | Document DB | SSPL v1 (not OSI) | r9.0.8 | SSPL matters if you offer it as a service | [license](https://github.com/mongodb/mongo/blob/master/LICENSE-Community.txt) |
| Redis | KV/cache | RSALv2 or SSPLv1 or AGPLv3 (8.0+); 7.2 and earlier BSD | 8.10.3 (2026-10-26) | AGPL option added May 2025 | [LICENSE](https://github.com/redis/redis/blob/unstable/LICENSE.txt), [blog](https://redis.io/blog/agplv3/) |
| Valkey | Redis fork | BSD-3-Clause | 9.1.3 (2026-10-26) | Drop-in for most Redis clients | [repo](https://github.com/valkey-io/valkey) |
| Qdrant | Vector DB | Apache-2.0 | v1.20.0 (2026-10-22) | Separate service; adds a sync path | [repo](https://github.com/qdrant/qdrant) |
| Weaviate | Vector DB | BSD-3 outside `wl/`; `wl/` is enterprise-only | v1.40.5 (2026-11-10) | Some features need a license key | [LICENSE](https://github.com/weaviate/weaviate/blob/main/LICENSE) |
| LanceDB | Embedded vector store | Apache-2.0 | PyPI 0.41.0 (2026-10-29) | Embedded like SQLite; good for local agents | [repo](https://github.com/lancedb/lancedb) |
| Chroma | Vector DB | Apache-2.0 | 1.5.9 (2026-05-05) | Prototyping; slower release cadence lately | [repo](https://github.com/chroma-core/chroma) |
| ParadeDB `pg_search` | BM25 search in Postgres | AGPL-3.0 | v0.26.6 (2026-11-08) | AGPL; check obligations before bundling | [repo](https://github.com/paradedb/paradedb) |
| Meilisearch | Search engine | MIT core + BUSL-1.1 Enterprise Edition parts | v1.56.2 (2026-11-09) | Cloud from $20/month, 14-day trial | [LICENSE](https://github.com/meilisearch/meilisearch/blob/main/LICENSE), [pricing](https://www.meilisearch.com/pricing) |
| Typesense | Search engine | GPL-3.0 | v30.2 (2026-04-19) | Self-host free | [repo](https://github.com/typesense/typesense) |
| OpenSearch | Search/log analytics | Apache-2.0 | 3.9.0 (2026-09-29); 2.19.7 | Heavy to run for a small app | [repo](https://github.com/opensearch-project/OpenSearch) |

When a separate vector DB is justified [inference]: the HNSW index no longer fits in RAM next to OLTP data, vector QPS interferes with transactional load, or you need features pgvector lacks after measuring. Until then, pgvector keeps vectors transactional with the rows they describe.

## 3. Licensing watchlist (2024-2026 changes)

- **Redis**: 7.4 moved to RSALv2/SSPL (March 2024). Redis 8 adds AGPLv3 as a third option. Valkey stays BSD ([Redis](https://redis.io/blog/agplv3/)).
- **Liquibase**: Community 5.0+ is FSL-1.1-ALv2 (Functional Source License that converts to Apache-2.0 later). Pro features were removed from GitHub releases ([LICENSE](https://github.com/liquibase/liquibase/blob/master/LICENSE.txt), [blog](https://www.liquibase.com/blog/liquibase-community-for-the-future-fsl)).
- **Atlas**: the standard binary is under the Atlas MSA. Only the Community build is Apache-2.0, and it lacks views, triggers, functions, RLS, extensions, partitions, `migrate lint`, and declarative `schema plan` ([Atlas editions](https://atlasgo.io/community-edition)).
- **Meilisearch** (MIT + BUSL EE), **Weaviate** (BSD + proprietary `wl/`), **TimescaleDB** (Apache + TSL): mixed-license repos, so check which features you enable.
- **MongoDB** SSPL, **Citus** and **ParadeDB** AGPL-3.0: fine for internal use. Get legal review before offering them as a service.
- **Ownership changes**: Neon now markets itself as "from Databricks" (Lakebase Postgres) ([Neon](https://neon.com/pricing)). Supabase is acquiring Turso ([Turso](https://turso.tech/blog/turso-is-joining-supabase)). Re-check terms after acquisitions.

## 4. Hosted free tiers (exact limits, 2026-11-11)

| Service | Free tier | Branching / backups on free | Gotchas | Source |
|---|---|---|---|---|
| Neon | 100 projects; 10 branches/project; 100 CU-hours/project/month; up to 2 CU; 1 GB storage/project, 20 GB total; 5 GB egress/project | Branching yes; 6 h history window (1 GB); 1 manual snapshot | Scales to zero after 5 min, no pausing for inactivity; hitting limits suspends compute or blocks writes, no data deleted | [pricing](https://neon.com/pricing) |
| Supabase | 2 active projects; 500 MB DB; shared CPU/500 MB RAM; 5 GB egress; 1 GB file storage; 50k MAU | No branching (Pro: $0.01344/branch-hour); no backups; PITR $100/month per 7 days | Free projects pause after 1 week of inactivity | [pricing](https://supabase.com/pricing) |
| Turso | 100 DBs; 5 GB; 500M rows read and 10M rows written per month; 3 GB syncs | 1-day point-in-time restore | SQLite semantics; vendor acquired by Supabase | [pricing](https://turso.tech/pricing) |
| Cloudflare D1 | 10 DBs; 5M rows read/day; 100k rows written/day; 5 GB total | n/a | Daily limits reset 00:00 UTC; queries error when exceeded; billed by rows scanned, so missing indexes cost money | [pricing](https://developers.cloudflare.com/d1/platform/pricing/) |
| Prisma Postgres | 200k operations/month; 2 GB; 50 DBs; 10 pooled + 10 direct connections | No backups on free (paid: daily, 7 days) | Accelerate retires 2026-12-01 | [pricing](https://www.prisma.io/pricing) |
| Nile | $0: 50M query tokens, 1 GB storage | Pricing page lists branching and backups as "coming soon" [unverified whether current] | Tenant-aware Postgres | [pricing](https://www.thenile.dev/pricing) |
| Xata | No free cloud tier (trial only); open-source self-host is free (Apache-2.0) | Copy-on-write branching on every plan | Cloud micro $0.012/h (~$9/month) + $0.28/GB-month | [pricing](https://xata.io/pricing) |
| PlanetScale | **None**: Hobby plan retired 2024-04-08 | n/a | Cheapest Postgres single-node PS-5 $5/month; HA PS-5 $15/month (us-east-1) | [blog](https://planetscale.com/blog/planetscale-forever), [pricing](https://planetscale.com/pricing) |
| MotherDuck | Lite $0: 10 GB, 10 h Pulse compute/month, 3 users | 1-day snapshot retention | Analytics only | [pricing](https://motherduck.com/product/pricing/) |

## 5. Branching, local dev, and tests

| Need | Pick | Notes | Source |
|---|---|---|---|
| Preview DB per PR | Neon branch (copy-on-write) or Supabase preview branch (paid) | Supabase preview branches are deleted when the PR merges or closes; persistent branches for staging | [Supabase branching](https://supabase.com/docs/guides/deployment/branching) |
| Branch per agent task | Neon branch, Xata branch, or Prisma `npx create-db --json` throwaway | Neon free includes 10 branches/project; extra branches $1.50/branch-month on paid | [Neon](https://neon.com/pricing), [Prisma blog](https://www.prisma.io/blog/agents-md-for-databases) |
| Local Postgres matching prod | Docker `postgres:18` (same major and extensions as prod) | On Windows, Docker Desktop + WSL2 is required for Testcontainers too [inference] | [Testcontainers](https://testcontainers.com/) |
| Integration tests | Testcontainers (node v12.2.1, go v0.45.0, python 4.15.0) | Real engine, disposable per test run | [node](https://github.com/testcontainers/testcontainers-node), [go](https://github.com/testcontainers/testcontainers-go), [python](https://github.com/testcontainers/testcontainers-python) |
| Fast in-process Postgres for unit tests or the browser | PGlite 0.5.16 (Apache-2.0) | WASM Postgres in single-user mode, ~3 MB gzipped, supports pgvector and PostGIS; not a load or concurrency test | [pglite](https://github.com/electric-sql/pglite) |
| Supabase stack locally | Supabase CLI (`supabase start`) | Local MCP at `http://localhost:54321/mcp` | [Supabase MCP](https://supabase.com/docs/guides/ai-tools/mcp) |

## 6. Repo organization (monorepo `packages/db`)

```text
packages/db/
  package.json          # "@acme/db": exports client, schema, generated types
  src/schema/           # Drizzle schema files (or prisma/schema.prisma)
  src/client.ts         # the ONLY place that reads DATABASE_URL and builds the pool
  migrations/           # generated SQL, committed, reviewed; never edited after merge
  seed/                 # deterministic, idempotent dev/test seed; refuses to run when NODE_ENV=production
  test/                 # integration tests against real Postgres (Testcontainers / branch)
  drizzle.config.ts     # or prisma.config.ts (Prisma 7 moves URLs here)
apps/api, apps/worker   # import @acme/db; never open their own connections
```

- Keep one owner of the schema (`packages/db`). Apps import the typed client and never run DDL [inference].
- Python services: `db/` package with SQLAlchemy models + `alembic/` versions dir. Go: `db/migrations` (goose or dbmate) + `db/queries` for sqlc [inference].
- Separate env vars: `DATABASE_URL` (pooled, app role) and `DIRECT_DATABASE_URL` (unpooled, owner role, migrations only). In Prisma 7, the URL in `prisma.config.ts` is the one the CLI uses for migrations ([Prisma 7 upgrade](https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7)).

## 7. Migrations

| Tool | Style | License | Latest | Agent notes | Source |
|---|---|---|---|---|---|
| Drizzle Kit | Codebase-first: `generate` SQL + `migrate`, or `push` | Apache-2.0 | 0.31.11 (latest), 1.0.0-rc.5 (2026-10-21) | `push --force` auto-approves data-loss statements; keep `push` for local prototyping | [migrations](https://orm.drizzle.team/docs/migrations), [push](https://orm.drizzle.team/docs/drizzle-kit-push) |
| Prisma Migrate | Schema-first, generated SQL | Apache-2.0 | 7.10.1 (2026-10-15); 8.0.0-rc.33 | Since 6.15, detects AI agents and refuses `migrate reset --force` without explicit consent | [changelog](https://www.prisma.io/changelog/2025-08-27) |
| Atlas | Declarative or versioned, lint, drift | Apache-2.0 Community build / MSA standard | v1.3.0 (2026-08-02) | Lint, `schema plan`, and RLS/views are paid (Pro, 30-day trial) | [editions](https://atlasgo.io/community-edition) |
| Alembic | SQLAlchemy autogenerate | MIT | 1.20.1 (2026-10-22) | Autogenerate output must be reviewed; it guesses renames as drop+add [inference] | [repo](https://github.com/sqlalchemy/alembic) |
| goose | SQL or Go migrations | MIT | v3.30.0 (2026-11-10) | Go-native; embeddable | [repo](https://github.com/pressly/goose) |
| dbmate | Plain SQL up/down, language-agnostic | MIT | v2.38.1 (2026-11-09) | Good default for polyglot repos | [repo](https://github.com/amacneil/dbmate) |
| sqitch | Dependency-based plans | MIT | v1.6.1 (2026-01-06) | Powerful, steeper learning curve | [repo](https://github.com/sqitchers/sqitch) |
| Flyway Community | Versioned SQL | Apache-2.0 | 13.12.1 (2026-11-05) | Undo and advanced features are in paid Redgate editions | [repo](https://github.com/flyway/flyway), [editions](https://www.red-gate.com/products/flyway/pricing) |
| Liquibase Community | Changelogs | FSL-1.1-ALv2 since 5.0 | v5.0.4 (2026-08-20) | License change; check policy | [LICENSE](https://github.com/liquibase/liquibase/blob/master/LICENSE.txt) |
| pgroll | Zero-downtime expand/contract for Postgres | Apache-2.0 | v0.16.3 (2026-09-08) | Serves old and new schema versions at once | [repo](https://github.com/xataio/pgroll) |
| Squawk | Postgres migration linter | Apache-2.0 | v2.72.0 (2026-11-08) | Free CI gate for lock-heavy DDL | [repo](https://github.com/sbdchd/squawk) |

| Stack | Access layer | Migration tool | Why |
|---|---|---|---|
| TypeScript, SQL-literate team, serverless/edge | Drizzle ORM | Drizzle Kit `generate` + `migrate` | SQL-shaped API; SQL files committed ([docs](https://orm.drizzle.team/docs/migrations)) |
| TypeScript, wants highest-level API and Studio | Prisma ORM 7 | Prisma Migrate | Built-in AI guardrail; Prisma 7 requires driver adapters ([upgrade](https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7)) |
| TypeScript, raw-SQL control | Kysely + kysely-codegen | dbmate or Atlas | Type-safe query builder; types generated from the live schema |
| Python | SQLAlchemy 2.x (or SQLModel with FastAPI) | Alembic | De facto standard pair |
| Go | sqlc (or ent) | goose / dbmate (or Atlas for ent) | sqlc compiles SQL to typed Go ([sqlc](https://github.com/sqlc-dev/sqlc)) |
| Polyglot monorepo | per-language layer | dbmate or Atlas on plain SQL | One SQL migration history shared by all services [inference] |

Expand-contract rules (zero-downtime) ([ParallelChange](https://martinfowler.com/bliki/ParallelChange.html), [GitLab](https://docs.gitlab.com/development/database/avoiding_downtime_in_migrations/)):
1. Expand: add the new column/table as nullable or defaulted. Deploy code that writes both old and new.
2. Backfill in batches. Switch reads. Then add constraints as `NOT VALID` and `VALIDATE CONSTRAINT` separately ([ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)).
3. Contract in a **later** release: stop referencing the old column in code first, drop it next release. GitLab splits a column drop across three releases.
4. Renames are add-copy-switch-drop, never `RENAME` while old code still runs.
5. Build indexes with `CREATE INDEX CONCURRENTLY`. It cannot run inside a transaction block, so mark that migration non-transactional ([CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html)).
6. Start every migration with `SET lock_timeout = '5s';` so it fails fast instead of queueing behind long queries and blocking all traffic ([client config](https://www.postgresql.org/docs/current/runtime-config-client.html)). Retry with backoff.
7. Migrations are forward-only once merged. Fix mistakes with a new migration, and never edit an applied file.

## 8. Schema conventions

- **Naming**: `snake_case`, unquoted, plural or singular consistently. Unquoted identifiers fold to lower case, and names are truncated at 63 bytes ([lexical](https://www.postgresql.org/docs/current/sql-syntax-lexical.html)). Name constraints explicitly (`orders_customer_id_fkey`) so migrations can reference them.
- **IDs**: Postgres 18 ships `uuidv7()`, time-ordered with millisecond precision ([UUID functions](https://www.postgresql.org/docs/18/functions-uuid.html)). Use `id uuid PRIMARY KEY DEFAULT uuidv7()`. `uuid_extract_timestamp()` reveals creation time, so do not expose v7 IDs where creation time is sensitive. On older Postgres, generate v7 in the app. `bigint GENERATED ALWAYS AS IDENTITY` is fine for internal tables [inference].
- **Timestamps**: `timestamptz` with `created_at`/`updated_at` set by the database, not the client [inference].
- **Soft delete**: usually not worth it. `deleted_at` leaks into every query, effectively loses foreign-key integrity, and makes pruning hard. Prefer hard delete plus a deleted-records table holding row JSON ([brandur](https://brandur.org/soft-deletion)). If you must soft delete, add partial unique indexes `WHERE deleted_at IS NULL` [inference].
- **Audit**: append-only `audit_log(table, row_id, op, old jsonb, new jsonb, actor, at)` written by trigger. Pass the actor via `set_config('app.actor_id', ..., true)` [inference].
- **Seeding**: deterministic, idempotent, small. Drizzle ships seeding docs ([seed](https://orm.drizzle.team/docs/seed-overview)) and Prisma has `prisma db seed`. Seeds never target production.
- **Domain modeling**: enums/`CHECK` constraints and foreign keys encode invariants. This builds on deep-mode's model-the-domain principle rather than repeating it.

## 9. Multi-tenancy

| Tenancy | Pattern | Why | Source |
|---|---|---|---|
| Many small tenants (B2C, SMB SaaS) | Pool: shared tables + `tenant_id` + RLS | One schema, one migration; the DB filters rows even when app code forgets the `WHERE` (not a boundary against arbitrary SQL, see below) | [AWS pool model](https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-managed-postgresql/pool.html), [AWS RLS blog](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/) |
| Few large or regulated tenants, residency, per-tenant restore | Silo: database per tenant | Strongest isolation; migrations fan out per DB | [AWS isolation whitepaper](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/pooled-storage-isolation-strategies.html), [Neon per-tenant cost](https://neon.com/pricing) |
| Mixed tiers | Bridge: schema per tenant or pool plus silo for premium | AWS describes mixing silo and pool | [AWS whitepaper PDF](https://docs.aws.amazon.com/pdfs/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.pdf) |
| Per-agent or per-user scratch data | SQLite DB per agent (Turso/D1) or Neon project | Cheap at high DB counts | [Turso](https://turso.tech/pricing), [D1](https://developers.cloudflare.com/d1/platform/pricing/) |

RLS facts that bite ([RLS docs](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)): superusers and `BYPASSRLS` roles always bypass RLS. Table owners bypass unless you use `FORCE ROW LEVEL SECURITY`. With no policy, access is default-deny. `TRUNCATE` is not subject to RLS. Supabase's `service_role` bypasses RLS ([General Analysis](https://generalanalysis.com/blog/supabase-mcp-blog)).

```sql
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON invoices
  USING (tenant_id = current_setting('app.tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
-- per request, inside the transaction (is_local = true survives transaction pooling):
SELECT set_config('app.tenant_id', $1, true);
```

Trust boundary: any role can set a custom setting such as `app.tenant_id` ([set_config](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-SET)). This policy stops app bugs that omit the tenant filter. It does not stop a caller that can run arbitrary SQL as `app_rw` or `agent_ro`, such as SQL injection or an agent with a SQL tool: that caller calls `set_config` with another tenant's UUID and reads that tenant's rows. Never give agents a SQL connection to pooled multi-tenant data. Where the caller can run arbitrary SQL, key isolation on something it cannot change: a separate database per tenant (silo), or one `LOGIN` role per tenant, with no membership in other tenant roles, and the policy keyed on `current_user`.

## 10. Access layers (ORMs, query builders, type generation)

| Tool | Lang | License | Latest | Agent notes | Source |
|---|---|---|---|---|---|
| Drizzle ORM | TS | Apache-2.0 | 0.45.4 (2026-10-08); 1.0.0-rc.5 | v1 RC changes relations API (RQB v2); pin a major | [repo](https://github.com/drizzle-team/drizzle-orm), [v1 upgrade](https://orm.drizzle.team/docs/upgrade-v1) |
| Prisma ORM 7 | TS | Apache-2.0 | 7.10.1; 8.0.0-rc.33 (2026-11-06) | 7: ESM-only, Rust-free `prisma-client` generator, required `output`, driver adapters for every DB, `prisma.config.ts`, no automatic `.env` loading, `pg` pool defaults (no connect timeout) | [upgrade](https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7) |
| Kysely | TS | MIT | 0.29.8 (2026-11-01) | Pair with kysely-codegen 0.20.0 (2026-02-16), kysely-ctl, or prisma-kysely 3.2.1 | [kysely](https://github.com/kysely-org/kysely), [codegen](https://github.com/RobinBlomberg/kysely-codegen) |
| Kanel | TS types from Postgres | MIT | npm 4.0.5 (2026-11-11) | GitHub releases stale (2023); npm is current | [repo](https://github.com/kristiandupont/kanel) |
| SQLAlchemy 2.x | Py | MIT | 2.1.8 / 2.0.57 (2026-11-04) | Use 2.0-style `select()`; async via asyncpg/psycopg 3 | [repo](https://github.com/sqlalchemy/sqlalchemy) |
| SQLModel | Py | MIT | 0.0.49 (2026-11-11) | Still 0.0.x; pin exact version | [repo](https://github.com/fastapi/sqlmodel) |
| sqlc | Go/others | MIT | v1.31.1 (2026-04-22) | Write SQL, get typed code; strong fit for agents because the SQL is reviewable [inference] | [repo](https://github.com/sqlc-dev/sqlc) |
| GORM | Go | MIT | v1.31.2 (2026-06-25) | Do not use `AutoMigrate` in production; use goose/Atlas [inference] | [repo](https://github.com/go-gorm/gorm) |
| ent | Go | Apache-2.0 | v0.14.6 (2026-03-23) | Schema-as-code; integrates with Atlas | [repo](https://github.com/ent/ent) |
| Diesel | Rust | MIT/Apache-2.0 | v2.3.14 (2026-10-07) | Compile-time checked queries | [repo](https://github.com/diesel-rs/diesel) |
| SeaORM | Rust | MIT/Apache-2.0 | 2.0.4 (2026-09-27) | Async ORM | [repo](https://github.com/SeaQL/sea-orm) |
| Supabase CLI types | TS | MIT | v4.0.0-next tags | `supabase gen types` from the live schema | [repo](https://github.com/supabase/cli) |

## 11. Operations: backups, PITR, pooling

- **Backups**: managed providers differ sharply. Neon keeps history for 6 h on free and up to 7/30 days on Launch/Scale. Supabase Pro has daily backups (7 days) and sells PITR as a $100/month add-on. Turso free has 1-day restore. Prisma Postgres free has none ([Neon](https://neon.com/pricing), [Supabase](https://supabase.com/pricing), [Turso](https://turso.tech/pricing), [Prisma](https://www.prisma.io/pricing)).
- Self-hosted Postgres: continuous WAL archiving + base backups give PITR ([docs](https://www.postgresql.org/docs/current/continuous-archiving.html)). Tools: pgBackRest 2.60.0 (MIT, 2026-10-18), WAL-G v3.0.9 (2026-08-20), Barman 3.20.1 (GPL-3.0) ([pgBackRest](https://github.com/pgbackrest/pgbackrest), [WAL-G](https://github.com/wal-g/wal-g), [Barman](https://github.com/EnterpriseDB/barman)). SQLite: Litestream.
- An untested backup is not a backup. Schedule a restore into a branch or scratch instance and run a row-count/checksum query [inference].
- **Pooling**: serverless functions must go through a pooler. PgBouncer 1.26.1 (2026-10-14) in transaction mode tracks protocol-level prepared statements when `max_prepared_statements` is non-zero (current default 200) ([config](https://www.pgbouncer.org/config.html)). Supavisor v2.10.0 (Apache-2.0) backs Supabase ([repo](https://github.com/supabase/supavisor)). Neon pools up to 10,000 connections per compute ([Neon](https://neon.com/pricing)). The Neon serverless driver 1.2.0 (MIT) works over HTTP/WebSocket ([repo](https://github.com/neondatabase/serverless)).
- Transaction pooling breaks session state. Use `set_config(..., true)`/`SET LOCAL` inside transactions, and route advisory locks, `LISTEN`, and migrations through the direct URL [inference].

## 12. Agents and databases

| MCP option | Read-only control | License / latest | Status | Source |
|---|---|---|---|---|
| Supabase MCP (hosted `mcp.supabase.com/mcp` or local CLI) | `read_only=true` runs SQL as a read-only Postgres user; `project_ref` scopes; `features=` limits tool groups | Apache-2.0; mcp-server-supabase v0.16.1 (2026-11-06) | Active; destructive-SQL confirmation is "not a security guarantee" | [docs](https://supabase.com/docs/guides/ai-tools/mcp), [repo](https://github.com/supabase-community/supabase-mcp) |
| Neon MCP (hosted `mcp.neon.tech/mcp`) | `readonly=true`, `projectId`, `category`, `roleName` (SQL runs as that role) | MIT repo; local stdio npm package deprecated | Neon: development and testing only, never connect to production | [docs](https://neon.com/docs/ai/neon-mcp-server) |
| Postgres MCP Pro (crystaldba) | `--access-mode=restricted`: read-only transactions + execution-time limits | MIT; v0.3.0 (2025-05-16) | **No release in 12+ months** | [repo](https://github.com/crystaldba/postgres-mcp) |
| Reference `@modelcontextprotocol/server-postgres` | READ ONLY transaction | MIT; npm 0.6.2 (2024-12-04) | **Archived**, "no security guarantees" | [archive](https://github.com/modelcontextprotocol/servers-archived) |
| MCP Toolbox for Databases (Google) | Tools defined in config [unverified details] | Apache-2.0; v1.16.0 (2026-11-05) | Active | [repo](https://github.com/googleapis/genai-toolbox) |

Incidents to learn from:
- **Supabase MCP, July 2025**: instructions planted in a support ticket made a developer's assistant, connected with `service_role` (bypasses RLS), read private tables and copy them into a customer-visible reply ([General Analysis](https://generalanalysis.com/blog/supabase-mcp-blog)). Supabase's response added read-only mode, project scoping, and feature groups, but states that prompt injection remains the top concern even in read-only mode ([Supabase](https://supabase.com/blog/defense-in-depth-mcp)).
- **Replit, July 2025**: an agent deleted a production database during a code freeze. Replit's fix was automatic dev/prod database separation ([Replit](https://replit.com/blog/introducing-a-safer-way-to-vibe-code-with-replit-databases), [CEO post](https://x.com/amasad/status/1946986468586721478)).

Least-privilege roles. Only the owner can DROP or ALTER an object; that right "cannot be granted or revoked" ([privileges](https://www.postgresql.org/docs/current/ddl-priv.html)). So app and agent roles must never own tables:

```sql
CREATE ROLE app_owner NOLOGIN;                 -- owns all objects; migrations SET ROLE app_owner
CREATE ROLE app_rw  LOGIN PASSWORD :'app_pw';  -- runtime: DML only, no TRUNCATE
CREATE ROLE agent_ro LOGIN PASSWORD :'agent_pw';
GRANT USAGE ON SCHEMA public TO app_rw, agent_ro;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_rw;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public GRANT SELECT ON TABLES TO agent_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_rw;
ALTER ROLE agent_ro SET default_transaction_read_only = on;
ALTER ROLE agent_ro SET statement_timeout = '5s';
```

On Neon, Console/API-created roles are members of `neon_superuser` and can read all data. Create agent roles with SQL or `neon roles create --access` ([Neon](https://neon.com/docs/ai/neon-mcp-server)). `pg_read_all_data` does not bypass RLS ([predefined roles](https://www.postgresql.org/docs/current/predefined-roles.html)).

Blocking dangerous operations, in layers:
1. **Database**: agents get a branch or throwaway DB plus a non-owner role. That alone makes `DROP`/`TRUNCATE` on prod impossible for them.
2. **Tooling**: Prisma refuses `migrate reset --force` when it detects an agent ([changelog](https://www.prisma.io/changelog/2025-08-27)). The agent should surface the prompt, not set the consent variable itself ([Prisma blog](https://www.prisma.io/blog/agents-md-for-databases)).
3. **Harness**: deny rules beat allow rules, e.g. Claude Code `"permissions": {"deny": ["Bash(npx prisma migrate reset:*)", "Bash(npx drizzle-kit push --force:*)", "Bash(dropdb:*)"]}` ([settings](https://code.claude.com/docs/en/settings)). Prefix patterns are bypassable through wrappers (`pnpm exec`, scripts), so treat them as a seatbelt, not a gate [inference].
4. **CI review gate**: lint every migration (Squawk free; Atlas `migrate lint` paid). Require human approval for files containing `DROP`, `TRUNCATE`, `ALTER ... TYPE`, or `SET NOT NULL` [inference].
5. **AGENTS.md**: state where scratch DBs come from, which commands need a human, and that tests run against real Postgres ([Prisma blog](https://www.prisma.io/blog/agents-md-for-databases)).

## Traps for agents

- Running `drizzle-kit push --force`, `prisma db push --accept-data-loss`, or `prisma migrate reset` to "fix" drift or a migration conflict, which wipes data. Generate a migration and ask instead ([Prisma blog](https://www.prisma.io/blog/agents-md-for-databases), [drizzle push](https://orm.drizzle.team/docs/drizzle-kit-push)).
- Using the first connection string found in `.env`, often production or `service_role`. Agents must only see branch/scratch URLs ([Neon](https://neon.com/docs/ai/neon-mcp-server), [General Analysis](https://generalanalysis.com/blog/supabase-mcp-blog)).
- Treating MCP read-only mode as safe: it stops writes, not exfiltration via prompt injection ([Supabase](https://supabase.com/blog/defense-in-depth-mcp)).
- Mocking the data layer or swapping in SQLite for Postgres tests. The result is green tests that miss constraint, RLS, and SQL-dialect bugs ([Prisma blog](https://www.prisma.io/blog/agents-md-for-databases)).
- Writing `RENAME COLUMN`/`DROP COLUMN` in the same deploy as the code change, or `CREATE INDEX` without `CONCURRENTLY` on a live table ([GitLab](https://docs.gitlab.com/development/database/avoiding_downtime_in_migrations/), [CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html)).
- Enabling RLS but connecting as the table owner or a `BYPASSRLS` role, so policies silently do nothing ([RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)).
- Copying Prisma 6 snippets into Prisma 7 projects (`prisma-client-js`, `datasourceUrl`, implicit `.env`). Writing new code against Accelerate URLs that retire 2026-12-01 ([upgrade](https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7)).
- Recommending PlanetScale "free tier" (gone since 2024), assuming Supabase free projects stay awake (they pause after 1 week), or quoting stale limits ([PlanetScale](https://planetscale.com/blog/planetscale-forever), [Supabase](https://supabase.com/pricing)).
- Picking a separate vector DB, search engine, or Redis on day one, which adds sync jobs and credentials that pgvector/FTS/Postgres would have avoided [inference].
- Choosing a stale or archived MCP server (reference Postgres server, LiteFS-era tooling) because it ranks high in training data ([archive](https://github.com/modelcontextprotocol/servers-archived)).
- Editing an already-applied migration file instead of adding a new one, which causes checksum drift and divergent environments [inference].
- Using `gen_random_uuid()` everywhere on Postgres 18 when `uuidv7()` exists, or exposing v7 IDs that leak creation time ([UUID functions](https://www.postgresql.org/docs/18/functions-uuid.html)).

## Default for a solo dev / small team

- **Database**: Postgres 18. Hosted on Neon Free for branching, or Supabase Free if you also want auth/storage (watch the 1-week pause). Prod moves to a paid plan with PITR before real users arrive.
- **Repo**: `packages/db` owns the schema, migrations, seed, client, and generated types. Apps import it.
- **TypeScript**: Drizzle ORM + Drizzle Kit `generate`/`migrate` (or Prisma 7 if the team prefers it). **Python**: SQLAlchemy 2 + Alembic. **Go**: sqlc + goose.
- **Extensions before services**: pgvector for embeddings, built-in FTS for search, pg_partman for big append tables, DuckDB locally for analytics.
- **Tenancy**: a `tenant_id` column + RLS with `FORCE ROW LEVEL SECURITY` from the first table; move to db-per-tenant only for contractual isolation.
- **IDs and data**: `uuidv7()` keys, `timestamptz`, hard delete plus an archive/audit table, deterministic seeds.
- **Safety**: three roles (owner, app, agent_ro), branch per PR/agent, Squawk in CI, human approval for destructive SQL, harness deny rules, monthly restore test.
- **Tests**: Testcontainers Postgres (or PGlite for fast unit tests) with migrations applied, never mocks.

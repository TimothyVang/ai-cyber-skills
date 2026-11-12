# Backend infrastructure and system design for agent-built apps (2026)

Strongest recommendations, checked 2026-11-11:
- Start as one deployable modular monolith on Postgres; split a service only when a named force (independent scaling, blast radius, team ownership) appears. Even the famous Prime Video case was one team collapsing a distributed pipeline into one process for a 90% cost cut ([Prime Video Tech](https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90)).
- Every remote call gets a timeout; retry at exactly one layer, with capped exponential backoff plus jitter, and only for idempotent operations ([AWS Builders' Library](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)).
- Background work: a Postgres-backed queue (pg-boss, River, Graphile Worker, pgmq) until you need multi-step, long-running, or human-wait flows; then a durable-execution engine (Temporal, DBOS, Hatchet, Restate, Inngest, Trigger.dev). Check each license: Restate is BSL, Inngest is SSPL.
- Instrument with OpenTelemetry from day one (traces and logs stable); define 1-3 SLOs and spend the error budget deliberately ([Google SRE book](https://sre.google/sre-book/service-level-objectives/)).
- Deploy containers to a PaaS (Fly.io, Railway, Render) or one VPS with Kamal/Coolify; skip Kubernetes until a team operates it; use OpenTofu (MPL-2.0) not Terraform (BSL) for new IaC.

Scope: this file adds primary-source, decision-ready infrastructure guidance. It builds on, and does not repeat, `references/domain-rules/backend-system-design.md` (API naming, indexing, cache-aside basics, queue basics), the `model-the-domain` principle, `references/cloud-devsecops/` (cloud security, CI/CD, IaC scanning, local emulators) and `references/credentials/` (secrets, auth). Prices and free tiers change monthly; re-check the cited page before committing a user to one.

## 1. Architecture shape

| Stage | Architecture | Infra | Why | Source |
|---|---|---|---|---|
| Prototype (0 users, 1 dev) | One process, one repo, one Postgres; modules by domain folder | PaaS free/hobby tier or one VPS | Boundaries are unknown; distribution would freeze wrong ones | [Fowler, MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html) |
| First users (1-10k, 1-5 devs) | Modular monolith + separate worker process from the same codebase; Postgres queue | PaaS paid tier or Kamal on 1-2 VMs; managed Postgres with PITR | Two process types cover web + async; one deploy pipeline | [Shopify, Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity), [37signals, Kamal 2](https://dev.37signals.com/kamal-2) |
| Growth (several teams, one hot path) | Extract only the module with a distinct scaling, release, or isolation need; keep the rest monolithic | Containers on managed orchestration (ECS, Cloud Run, or K8s if a team owns it); IaC | Split along proven seams; cost of a network hop is paid only where it buys something | [Prime Video Tech](https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90) |
| Large multi-tenant SaaS, strict blast-radius needs | Cell-based architecture: N identical stacks, thin router, tenant-to-cell mapping | Per-cell accounts or stacks | Limits a bad deploy or noisy tenant to one cell | [AWS cell-based whitepaper](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html) |

Rules:
- Fowler: almost all successful microservice stories started as a monolith that grew too big; teams that started with microservices often got into serious trouble ([MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)).
- Read the Prime Video case precisely: one audio/video monitoring service moved from Step Functions + Lambda components to a single ECS process; it is not "Amazon abandoned microservices" ([Prime Video Tech](https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90)).
- Enforce module boundaries in code, not by network. Shopify's 2024 Packwerk retrospective reports that "privacy checks" (public/private constants) became a shortcut that did not fix the real problem, which is the dependency graph ([Shopify](https://shopify.engineering/a-packwerk-retrospective)). TS equivalent [inference]: per-module `index.ts` public API plus a lint rule (eslint `no-restricted-imports` or dependency-cruiser) banning deep imports.
- "Majestic monolith": a small team gains more from one coherent app than from service boundaries it cannot staff ([DHH](https://signalvnoise.com/svn3/the-majestic-monolith/)).
- Split triggers (need at least one, written down in an ADR) [inference]: different scaling profile (CPU-bound media vs I/O web), different release cadence or owner team, regulatory isolation, different runtime language, or a failure domain that must not take down the core.
- Cells are for blast-radius limits at scale; the whitepaper itself frames them as a resiliency investment with routing, migration and observability costs ([AWS](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html)). Small apps: no cells; do keep a tenant ID on every row so cells stay possible [inference].
- Twelve-Factor still holds for config in env, stateless processes, backing services as attached resources, disposability, dev/prod parity, logs as event streams ([12factor.net](https://12factor.net/)). It was open-sourced on 2024-11-12 for community modernization ([announcement](https://12factor.net/blog/open-source-announcement)); the [twelve-factor repo](https://github.com/twelve-factor/twelve-factor) (CC-BY-4.0) has had no commit since 2025-07-10, so treat the revision as stalled and the original text as canonical.
- Hexagonal (ports and adapters): domain core depends on interfaces; DB, HTTP, queue are adapters. Use it at module edges that talk to external systems, not as layers of ceremony everywhere ([AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html)).

Modular monolith layout (TypeScript; same shape in Go `internal/<module>` or Python packages) [inference]:
```
apps/api/src/
  modules/billing/{index.ts, domain/, adapters/db.ts, adapters/stripe.ts, http.ts, jobs.ts}
  modules/catalog/{index.ts, ...}
  platform/{db.ts, queue.ts, telemetry.ts, config.ts}   # shared infra, no domain logic
  main.ts      # web process
  worker.ts    # job process, same image, different command
```
Each module owns its tables (prefix or schema); other modules call `modules/<x>/index.ts`, never its tables.

## 2. Reliability

Frameworks to check designs against (all free to read):

| Framework | Shape | Source |
|---|---|---|
| AWS Well-Architected | 6 pillars: operational excellence, security, reliability, performance efficiency, cost optimization, sustainability; framework doc dated 2024-11-06 | [AWS](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) |
| Azure Well-Architected | 5 pillars: reliability, security, cost optimization, operational excellence, performance efficiency | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/well-architected/) |
| Google Cloud Well-Architected (renamed from Architecture Framework) | Pillars plus cross-pillar perspectives; changelog maintained | [Google Cloud](https://docs.cloud.google.com/architecture/framework) |
| Google SRE book + workbook | SLIs, SLOs, error budgets, burn-rate alerting | [SLO chapter](https://sre.google/sre-book/service-level-objectives/), [Implementing SLOs](https://sre.google/workbook/implementing-slos/) |

SLO method:
- SLI = good events / valid events, measured as close to the user as possible (load balancer or client), e.g. "HTTP 2xx/3xx/4xx under 300 ms / all requests" ([SRE book](https://sre.google/sre-book/service-level-objectives/)).
- SLO = target over a window (e.g. 99.5% over 28 days). Error budget = 1 - SLO. Write an error budget policy: the workbook example requires a postmortem when one incident burns over 20% of the 4-week budget ([SRE workbook](https://sre.google/workbook/error-budget-policy/)).
- Alert on burn rate with multiple windows (fast burn pages, slow burn tickets), not on raw CPU ([SRE workbook, Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)).

Timeouts, retries, backoff (from [AWS Builders' Library](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)):
- Set connect and request timeouts on every remote call, including cross-process on one host. Pick the value from the dependency's latency at your acceptable false-timeout rate (Amazon example: 0.1% -> use p99.9), padded for internet clients.
- Retries multiply: 5 layers x 3 tries = 243x load on the database. Retry at one layer only.
- Use capped exponential backoff with jitter; also jitter cron and periodic jobs.
- Amazon prefers a local token bucket that limits retries over circuit breakers, because breakers add hard-to-test modal behavior. This refines the existing deep-mode "circuit breaker on every third-party call" rule: use a retry budget first, add a breaker where a fallback exists ([Azure circuit breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)).
- Do not retry non-idempotent calls; 4xx are generally not retryable, 429/503 are, honoring `Retry-After` ([RFC 9110](https://www.rfc-editor.org/rfc/rfc9110)).

```ts
// full jitter: sleep = random(0, min(cap, base * 2^attempt))
const delay = (n: number, base = 100, cap = 10_000) => Math.random() * Math.min(cap, base * 2 ** n);
```

Idempotency:
- Client sends `Idempotency-Key` (Stripe: up to 255 chars, no PII); server stores key + request fingerprint + response; same key with different params is an error; v1 keys may be pruned after 24 hours ([Stripe API](https://docs.stripe.com/api/idempotent_requests)). Design write-up: [Stripe blog](https://stripe.com/blog/idempotency), [AWS Builders' Library](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).
- Implementation [inference]: table `idempotency_keys(key, user_id, request_hash, status, response, created_at)`, unique on `(user_id, key)`, insert in the same transaction as the side effect.

Overload protection:
- Rate limiting: token bucket per API key/user; Stripe runs four limiters: request rate, concurrent requests, fleet-usage load shedder, worker-utilization load shedder ([Stripe](https://stripe.com/blog/rate-limiters)). Return 429 with `Retry-After`.
- Load shedding: reject early and cheaply when over capacity so accepted work still meets latency; prioritize health checks and paying traffic ([AWS Builders' Library](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)).
- Queues hide overload: bound queue depth, alarm on age of oldest message, and plan how to drain a backlog ([AWS Builders' Library](https://aws.amazon.com/builders-library/avoiding-insurmountable-queue-backlogs/)).
- Graceful degradation: decide per feature what to drop (recommendations, search suggestions) when a dependency fails; serve stale cache rather than error [inference].

Health checks ([Kubernetes probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)):

| Probe | Answers | Must not |
|---|---|---|
| Liveness `/livez` | Is this process wedged (deadlock)? Restart it | Check the DB or other dependencies; docs warn misconfigured liveness probes cause cascading failures |
| Readiness `/readyz` | Can it take traffic now (warmed, connected)? | Fail permanently; it only removes the pod from load balancing |
| Startup | Slow boot finished? Delays liveness | Be omitted on apps with long migrations or cache warmup |

PaaS platforms (Fly, Render, Railway) use one HTTP health check; point it at readiness-style logic that stays cheap [inference].

## 3. Async work, workflows, scheduling

| Workload | Pick | Why | Source |
|---|---|---|---|
| Emails, webhooks out, thumbnails; already on Postgres | Postgres queue: pg-boss (Node), River (Go), Graphile Worker (Node), pgmq (any language, SQL API) | Enqueue in the same transaction as the business write: no outbox, no extra infra | [River transactional enqueueing](https://riverqueue.com/docs/transactional-enqueueing) |
| Multi-step, long-running, waits for humans/timers, must survive deploys | Durable execution (table below) | Engine checkpoints each step; code resumes after crash | [Lambda durable functions](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions.html) |
| Fan-out events to many consumers, replay, analytics | Kafka (or Redpanda), NATS JetStream lighter option | Durable partitioned log, consumer offsets | [Kafka 4.1 upgrade notes](https://kafka.apache.org/41/getting-started/upgrade/) |
| Task routing, priorities, RPC-ish messaging, polyglot | RabbitMQ | Mature broker, exchanges, quorum queues | [rabbitmq-server](https://github.com/rabbitmq/rabbitmq-server) |
| On AWS, no servers to run | SQS (+ DLQ) and EventBridge Scheduler | Managed, pay per request; set visibility timeout > job time | [SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html), [DLQ](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) |
| Cron | Queue library's scheduler (pg-boss, River, Graphile Worker all ship cron) or EventBridge Scheduler; never `setInterval` in a web replica | Exactly one firing across replicas; persisted schedule | [EventBridge Scheduler](https://docs.aws.amazon.com/eventbridge/latest/userguide/using-eventbridge-scheduler.html) |

Queues and streams (latest release from GitHub API, 2026-11-11):

| Tool | What | License | Latest | Agent notes | Source |
|---|---|---|---|---|---|
| pg-boss | Node job queue on Postgres, cron, retries | MIT | 12.38.2 (2026-11-10) | `SKIP LOCKED` based; very active; can enqueue on your own transaction's connection [unverified] | [repo](https://github.com/timgit/pg-boss) |
| River | Go job queue on Postgres, transactional enqueue | MPL-2.0 | v0.51.2 (2026-11-09) | Pre-1.0 API; pin versions | [repo](https://github.com/riverqueue/river) |
| Graphile Worker | Node job queue on Postgres, LISTEN/NOTIFY | MIT | v0.18.0 (2026-09-08) | Pre-1.0; good with any Node stack | [repo](https://github.com/graphile/worker) |
| pgmq | Postgres extension, SQS-like visibility timeout API | PostgreSQL | v1.13.1 (2026-10-20) | Repo moved to `pgmq/pgmq`; needs extension install (not on every managed PG) | [repo](https://github.com/pgmq/pgmq) |
| NATS JetStream | Lightweight pub/sub + persistent streams, KV | Apache-2.0 | v2.15.3 (2026-11-11) | Single Go binary; good self-host choice | [repo](https://github.com/nats-io/nats-server) |
| RabbitMQ | AMQP broker, streams | MPL-2.0 | v4.4.0 (2026-10-19) | Use quorum queues for durability | [repo](https://github.com/rabbitmq/rabbitmq-server) |
| Apache Kafka | Distributed log; KRaft-only since 4.0; share groups ("queues for Kafka") previewed in 4.1 | Apache-2.0 | 4.4.0 | Heavy for small teams; managed offerings cost money | [downloads](https://downloads.apache.org/kafka/), [4.1 notes](https://kafka.apache.org/41/getting-started/upgrade/) |
| Redpanda | Kafka-API compatible, C++ | Community: BSL (no offering as a service; converts to Apache-2.0 4 years after merge); Enterprise: RCL | v26.2.2 (2026-08-22) | Not OSI open source | [licensing](https://docs.redpanda.com/current/get-started/licensing/overview/) |

Durable execution engines:

| Tool | Model | License | Latest | Free tier (managed) | Source |
|---|---|---|---|---|---|
| Temporal | Workflows + activities, SDKs for Go/Java/Python/TS/.NET/Ruby/PHP; self-host server | MIT | v1.32.2 (2026-11-02) | $150 credits for 90 days, then pay-as-you-go from $0/mo, $50 per 1M actions (first 5M) | [pricing](https://temporal.io/pricing), [repo](https://github.com/temporalio/temporal) |
| DBOS Transact | Library; checkpoints workflows into your Postgres; no separate server | MIT | py 3.5.0 (2026-11-10) | Library free; Pro (Conductor tooling) $99/mo | [pricing](https://www.dbos.dev/pricing), [repo](https://github.com/dbos-inc/dbos-transact-py) |
| Hatchet | Task queue + workflows on Postgres | MIT | v0.114.2 (2026-10-26) | 1M runs + 1M events/mo free, then $30 per 1M runs | [pricing](https://hatchet.run/pricing), [repo](https://github.com/hatchet-dev/hatchet) |
| Restate | Durable handlers, virtual objects; single binary | BSL 1.1 with use grant: free in production except running a public Restate platform service | v1.8.1 (2026-10-21) | Cloud free plan 100k actions/mo | [pricing](https://restate.dev/pricing), [LICENSE](https://github.com/restatedev/restate) |
| Inngest | Event-driven step functions; serverless friendly | SSPL v1 with Apache-2.0 future license | v1.52.0 (2026-11-10) | Free 50k executions/mo, pauses at quota | [pricing](https://www.inngest.com/pricing), [repo](https://github.com/inngest/inngest) |
| Trigger.dev | TS background tasks, long runs on managed compute | Apache-2.0 | v4.8.4 (2026-11-10) | $5/mo compute credit, 20 concurrent runs | [pricing](https://trigger.dev/pricing), [repo](https://github.com/triggerdotdev/trigger.dev) |
| AWS Lambda durable functions | Checkpoint/replay steps, executions up to one year | Proprietary (paid service) | n/a | Lambda free tier: 1M requests + 400k GB-s/mo; durable ops billed separately | [docs](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions.html), [pricing](https://aws.amazon.com/lambda/pricing/) |
| Cloudflare Workflows | Durable steps on Workers | Proprietary (paid service) | n/a | See Workers plan limits | [docs](https://developers.cloudflare.com/workflows/) |

Pick rule [inference]: Python/TS app already on Postgres and small team -> DBOS or Hatchet (no new datastore). Polyglot or many long-lived workflows with a team to run it -> Temporal. TS-only, serverless host -> Inngest or Trigger.dev cloud. Need self-host without license questions -> Temporal, DBOS, Hatchet, Trigger.dev.

Transactional outbox (when the queue is not in your database) ([AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)):
```sql
-- one statement, one transaction: the event exists only if this call changed the order
WITH paid AS (
  UPDATE orders SET status = 'paid' WHERE id = $1 AND status = 'pending' RETURNING id
)
INSERT INTO outbox (id, topic, payload)
SELECT uuidv7(), 'order.paid', $2 FROM paid;  -- 0 rows: order missing or already paid; no event
-- relay: SELECT ... FROM outbox WHERE sent_at IS NULL ORDER BY id LIMIT 100 FOR UPDATE SKIP LOCKED; publish; mark sent
```
Guard the state transition (`status = 'pending'`) so a retried request inserts no second event, and check the inserted row count to tell the caller whether anything changed. `uuidv7()` (Postgres 18) is time-ordered, so the relay's `ORDER BY id` approximates insert order; on older Postgres generate v7 IDs in the app. Consumers must still be idempotent by event `id`: the relay delivers at least once ([AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)).

## 4. Caching and CDNs

- Cache-aside basics live in the existing backend file; here: name the invalidation trigger for every cached key (TTL only, write-through, or explicit delete on write) before adding the cache ([AWS caching patterns](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html)).
- HTTP caching is defined by [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111); practical guide: [MDN Caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching).

| Resource | Header | Why |
|---|---|---|
| Hashed static assets (`app.3f9a.js`) | `Cache-Control: public, max-age=31536000, immutable` | Filename changes on deploy |
| HTML shell | `Cache-Control: no-cache` + `ETag` | Revalidate each time, cheap 304 |
| Public API GET, tolerant of staleness | `Cache-Control: public, s-maxage=60, stale-while-revalidate=300` | CDN absorbs bursts |
| Per-user or authenticated data | `Cache-Control: private, no-store` (or `private, max-age=0`) | Prevents shared caches leaking data |

- Put a CDN in front of static assets from day one (most PaaS and Cloudflare free plans do this) [inference]. Never let a CDN cache responses that vary by `Authorization` or cookies without `Vary` or `private` ([RFC 9111](https://www.rfc-editor.org/rfc/rfc9111)).

## 5. API styles and design

| Situation | Pick | Why | Source |
|---|---|---|---|
| Public or third-party API, webhooks, mixed clients | REST + OpenAPI 3.1/3.2 | Universal tooling, HTTP caching, codegen | [OAS 3.2.0](https://spec.openapis.org/oas/v3.2.0.html) |
| TS frontend and TS backend in one repo, no external consumers | tRPC | End-to-end types without codegen; not for public APIs | [tRPC docs](https://trpc.io/docs) |
| Internal service-to-service, polyglot, streaming | gRPC (protobuf) | Contracts, codegen, HTTP/2 streaming | [gRPC intro](https://grpc.io/docs/what-is-grpc/introduction/) |
| Many client shapes over a rich graph, a team to run it | GraphQL | Client-selected fields; needs query cost limits and persisted queries | [GraphQL spec](https://spec.graphql.org/) |

- OpenAPI 3.2.0 shipped 2025-09-19 (streaming/sequential media types, `QUERY` method, hierarchical tags); 3.2.1 is the latest patch ([OAI announcement](https://www.openapis.org/blog/2025/09/23/announcing-openapi-v3-2), [release](https://github.com/OAI/OpenAPI-Specification/releases/tag/3.2.0)). Use 3.1 when your generator lacks 3.2 support [inference].
- Style guides to follow instead of inventing rules: [Google AIP](https://google.aip.dev/158) (resource-oriented, 158 pagination, 193 errors, 185 versioning), [Microsoft API guidelines](https://github.com/microsoft/api-guidelines), [Zalando RESTful guidelines](https://opensource.zalando.com/restful-api-guidelines/).
- Pagination: cursor/page-token, not offset, for anything that grows; return `next_page_token`, treat it as opaque, cap `page_size` ([AIP-158](https://google.aip.dev/158)).
- Versioning: major version in the path (`/v1`), additive changes only within a version ([AIP-185](https://google.aip.dev/185)); Stripe-style dated versions are an option for a public API with many integrators [inference].
- Errors: `application/problem+json` per [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) (obsoletes RFC 7807):
```json
{"type":"https://example.com/problems/insufficient-funds","title":"Insufficient funds","status":403,"detail":"Balance 30, cost 50","instance":"/v1/payments/abc"}
```

## 6. Observability

OpenTelemetry signal status ([spec status](https://opentelemetry.io/docs/specs/status/)): traces API/SDK/protocol stable; metrics API and protocol stable, SDK mixed; logs bridge API, SDK, protocol stable (use your normal logger plus an OTel appender, not the bridge API directly); profiles in development, public alpha announced 2026 ([OTel blog](https://opentelemetry.io/blog/2026/profiles-alpha/)). Collector is still 0.x (v0.165.0, 2026-11-06) ([repo](https://github.com/open-telemetry/opentelemetry-collector)).
- Rules: structured JSON logs with `trace_id`/`span_id`; follow [semantic conventions](https://opentelemetry.io/docs/specs/semconv/) for attribute names; export OTLP to a Collector so the backend is swappable; sample traces at the head only after volume forces it [inference].

| Tool | What | License | Latest | Agent notes | Source |
|---|---|---|---|---|---|
| Grafana LGTM (Loki, Grafana, Tempo, Mimir) | Logs, dashboards, traces, metrics | AGPL-3.0 | Loki v3.7.9, Tempo v3.1.1, Mimir 3.2.4 (Oct 2026) | Most moving parts; Grafana Cloud free tier exists (limits on vendor page) | [grafana.com/oss](https://grafana.com/oss/), [loki](https://github.com/grafana/loki) |
| SigNoz | OTel-native all-in-one on ClickHouse | MIT core, `ee/` dirs under enterprise license | v0.149.0 (2026-11-04) | Single docker-compose self-host | [repo](https://github.com/SigNoz/signoz) |
| OpenObserve | Logs/metrics/traces, object-storage backed | AGPL-3.0 | v1.2.0-rc1 (2026-11-04, pre-release) | Lightest single binary | [repo](https://github.com/openobserve/openobserve) |
| Uptrace | OTel APM on ClickHouse | AGPL-3.0 | v2.1.0-rc.2 (2026-10-22, pre-release) | Smaller community | [repo](https://github.com/uptrace/uptrace) |
| Sentry (self-hosted) | Errors, performance, replays | FSL-1.1-Apache-2.0 (source-available; each release becomes Apache-2.0 after 2 years); AI features closed | 26.10.1 (2026-10-29) | Self-host is heavy (many containers); SaaS free tier is easier | [licensing](https://open.sentry.io/licensing), [self-hosted](https://github.com/getsentry/self-hosted) |

AGPL is fine for running unmodified backends internally; modifying and offering them as a network service triggers source obligations [inference; check with counsel].

## 7. Deployment and infrastructure

| Situation | Pick | Why | Source |
|---|---|---|---|
| Solo dev, wants zero ops | Render or Railway (git push deploys, managed Postgres) | Hobby/free entry points; previews | [Render pricing](https://render.com/pricing), [Railway pricing](https://railway.com/pricing) |
| Needs regions near users, long-lived processes, volumes | Fly.io | Pay-as-you-go, no platform fee; $1 trial credit; managed Postgres from $38/mo | [Fly pricing](https://fly.io/docs/about/pricing/), [free trial](https://fly.io/docs/about/free-trial/) |
| Cost-sensitive, own VPS (Hetzner etc.) | Kamal (CLI, SSH + Docker) or Coolify/Dokploy (self-hosted PaaS UI) | Fixed cost, no lock-in; you own patching and backups | [Kamal](https://kamal-deploy.org/), [Coolify pricing](https://coolify.io/pricing) |
| Spiky, stateless HTTP, edge latency | Cloudflare Workers | Free: 100k requests/day, 10 ms CPU per invocation | [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) |
| Event glue on AWS | Lambda | Free tier 1M requests + 400k GB-s/mo; cold starts, 15-min max (durable functions extend) | [Lambda pricing](https://aws.amazon.com/lambda/pricing/) |
| Many services, platform team exists | Kubernetes (managed: EKS/GKE/AKS) | Standard scheduling, probes, rollouts; real ops cost | [K8s probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/) |

- Free tier caveats: Render free web services spin down after 15 minutes idle and take time to wake ([Render](https://render.com/docs/free)); Railway's free plan is a 30-day trial with $5 credit, then $1/mo with 0.5 GB RAM per service ([Railway](https://railway.com/pricing)).

| Tool | What | License | Latest | Agent notes | Source |
|---|---|---|---|---|---|
| Kamal | Zero-downtime Docker deploys to any host via SSH, kamal-proxy | MIT | v2.12.0 (2026-06-18) | Runs HEY and Basecamp; needs a registry | [repo](https://github.com/basecamp/kamal) |
| Coolify | Self-hosted PaaS (Heroku-like UI) | Apache-2.0 | v4.7.5 (2026-11-10) | Self-host free; cloud from $5/mo | [repo](https://github.com/coollabsio/coolify) |
| Dokploy | Self-hosted PaaS on Docker Swarm | Apache-2.0 except `/proprietary` dirs | v0.31.0 (2026-11-05) | Check which features sit in proprietary dirs | [repo](https://github.com/Dokploy/dokploy) |
| OpenTofu | Terraform-compatible IaC, Linux Foundation | MPL-2.0 | v1.13.9 (2026-11-05) | Default for new IaC; `tofu` CLI | [docs](https://opentofu.org/docs/intro/), [repo](https://github.com/opentofu/opentofu) |
| Terraform | HashiCorp/IBM IaC | BSL 1.1 since 1.6.0 (licensor now IBM) | v1.17.2 (2026-11-11) | Fine to use internally; not OSI open source; competing-product limits | [LICENSE](https://github.com/hashicorp/terraform) |
| Pulumi | IaC in TS/Python/Go | Apache-2.0 | v3.274.1 (2026-11-05) | State in Pulumi Cloud (paid tiers) or self-managed backend | [repo](https://github.com/pulumi/pulumi) |
| SST | TS IaC for AWS/Cloudflare apps | MIT | v4.17.2 (2026-10-08) | Opinionated; good for serverless TS | [repo](https://github.com/sst/sst) |

Environments and releases:
- Three environments are enough: local (Docker Compose), preview per PR (Render/Railway/Fly support this), production; plus staging only if data migrations need rehearsal [inference]. Dev/prod parity: same Postgres major version and same container image ([12factor.net](https://12factor.net/)).
- Blue/green: two full stacks, switch traffic, keep old for rollback; canary: send a small slice, compare SLIs against the control, then widen ([SRE workbook, Canarying Releases](https://sre.google/workbook/canarying-releases/)). Kamal and PaaS do rolling/zero-downtime swaps; true canary needs weighted routing.
- Database changes use expand/contract: add column -> deploy code that writes both -> backfill -> switch reads -> drop old, so any two adjacent releases work against the same schema [inference].
- Feature flags decouple deploy from release; code against the vendor-neutral OpenFeature API (CNCF incubating) ([CNCF](https://www.cncf.io/projects/openfeature/), [spec](https://openfeature.dev/specification/)).

| Flag tool | License | Latest | Notes | Source |
|---|---|---|---|---|
| OpenFeature SDKs + flagd | Apache-2.0 | spec repo active (2026-11) | Standard API; flagd can serve flags from a JSON file in git | [spec](https://github.com/open-feature/spec) |
| Unleash | AGPL-3.0 per repo LICENSE | v8.3.1 (2026-10-29) | Self-host; enterprise features paid | [repo](https://github.com/Unleash/unleash) |
| Flagsmith | BSD-3-Clause | v2.290.0 (2026-11-05) | Most permissive self-host | [repo](https://github.com/Flagsmith/flagsmith) |
| GrowthBook | MIT core, enterprise dirs under commercial license | v5.2.0 (2026-11-03) | Flags + A/B experiments with stats | [repo](https://github.com/growthbook/growthbook) |

Rule: every flag has an owner and removal date; stale flags are dead code [inference].

## 8. Capacity and cost

Back-of-envelope method (Google's non-abstract large system design: estimate with real numbers, then iterate the design) ([SRE workbook NALSD](https://sre.google/workbook/non-abstract-design/)):
1. Requests: DAU x actions per user per day / 86,400 = average RPS; x3 to x10 for peak [inference].
2. Storage: rows per day x bytes per row x retention x (1 + index overhead, ~1x) [inference].
3. Bandwidth: peak RPS x response size.
4. Compare with one box: if peak RPS and data fit one Postgres + 2 app instances with headroom, stop designing for scale.
Worked example [inference]: 10k DAU x 50 req/day = 500k/day = ~6 RPS avg, ~60 RPS peak; 1 KB rows x 20k/day x 365 = ~7 GB/yr. One small managed Postgres covers it.

| Tool | What | License | Latest | Agent notes | Source |
|---|---|---|---|---|---|
| k6 | Load tests in JS, thresholds as pass/fail | AGPL-3.0 | v2.3.0 (2026-09-21) | Use test types: smoke, average-load, stress, spike, soak, breakpoint | [test types](https://grafana.com/docs/k6/latest/testing-guides/test-types/), [repo](https://github.com/grafana/k6) |
| Locust | Load tests in Python, distributed | MIT | 2.47.0 (2026-10-21) | Good for Python teams; user-behavior scripting | [docs](https://docs.locust.io/en/stable/), [repo](https://github.com/locustio/locust) |
| Vegeta | Constant-rate HTTP load CLI/library (Go) | MIT | v12.13.0 (2025-10-31) | No release in 12+ months (commits through 2026-09); fine for quick rate tests | [repo](https://github.com/tsenart/vegeta) |

- Load test against a production-like environment, with thresholds tied to SLOs (e.g. `p(95)<300`, error rate < 1%), never against third-party APIs you call [inference].

Cost guardrails:
- Set budgets and alerts on day one: [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html), [Railway usage limits](https://docs.railway.com/reference/usage-limits); prefer services that pause at quota (Inngest free plan, Hatchet) over ones that bill unbounded overage ([Inngest](https://www.inngest.com/pricing), [Hatchet](https://hatchet.run/pricing)).
- Well-Architected's cost pillar: tag resources by owner/env, review monthly, delete idle previews ([AWS](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)).
- Watch the usual surprises [inference]: egress (Fly $0.02/GB NA/EU, Railway $0.05/GB), NAT gateways, log ingestion volume, managed DB minimums, and preview environments left running ([Fly](https://fly.io/docs/about/pricing/), [Railway](https://railway.com/pricing)).

## Traps for agents
- Proposing microservices, Kafka, or Kubernetes for a new single-team app. Default to the modular monolith ([Fowler](https://martinfowler.com/bliki/MonolithFirst.html)); require a written split trigger.
- Citing Prime Video as "Amazon went back to monoliths"; it was one monitoring service ([Prime Video Tech](https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90)).
- Adding retries at every layer (SDK default + app loop + queue redelivery) and multiplying load; retrying POSTs without an idempotency key ([AWS Builders' Library](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)).
- Calling HTTP clients without a timeout: Python `requests` never times out unless `timeout=` is set ([Requests docs](https://requests.readthedocs.io/en/latest/user/quickstart/)); Node `fetch` defaults are minutes long [unverified]. Pass `AbortSignal.timeout(ms)` or `timeout=` explicitly.
- Liveness probes that check the database, so a DB blip restarts every pod ([Kubernetes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)).
- Publishing to a broker after `COMMIT` (dual write) instead of transactional enqueue or an outbox ([AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)).
- Running cron with `setInterval` inside web replicas (fires N times, dies on deploy).
- Calling BSL/SSPL/FSL tools "open source": Restate's pricing page says "permissive license" but the repo LICENSE is BSL 1.1 ([LICENSE](https://github.com/restatedev/restate)); Terraform and Redpanda are BSL, Inngest SSPL, Sentry FSL. Report the license from the repo, not the marketing page.
- Recommending Terraform for new code without noting OpenTofu, or writing `terraform` commands for a repo using `tofu` [inference].
- Offset pagination and ad-hoc error JSON in new APIs; use page tokens and RFC 9457 ([AIP-158](https://google.aip.dev/158), [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)).
- Caching authenticated responses at a CDN, or adding a cache with no invalidation story ([RFC 9111](https://www.rfc-editor.org/rfc/rfc9111)).
- Quoting free-tier numbers or plan names from training data; they change often. Fetch the pricing page and cite its date.
- Treating OTel metrics SDKs and profiles as uniformly stable; check the per-language README ([OTel status](https://opentelemetry.io/docs/specs/status/)).
- Leaving a deploy target on a free tier that sleeps (Render) for webhooks or cron, then missing events ([Render](https://render.com/docs/free)).

## Default for a solo dev / small team
- Shape: one repo, one container image, two commands (`web`, `worker`), modules by domain with an `index.ts` public API and a lint rule against deep imports.
- Data and jobs: managed Postgres with PITR; jobs via pg-boss or Graphile Worker (Node), River (Go), DBOS or pgmq over SQL (Python); enqueue inside the business transaction.
- Workflows: none until a flow spans minutes+ or waits on humans; then DBOS or Hatchet (MIT, Postgres) or Temporal Cloud ($150 credits).
- API: REST + OpenAPI 3.1, RFC 9457 errors, cursor pagination, `Idempotency-Key` on creates and payments; tRPC only for an internal TS-only frontend.
- Reliability: timeouts on every call, one retry layer with full jitter, 429 + `Retry-After`, `/livez` (no deps) and `/readyz`; one availability SLO and one latency SLO per user-facing API.
- Observability: OTel SDK + Collector -> SigNoz self-host or a vendor free tier; Sentry SaaS free tier for errors; JSON logs with trace IDs.
- Deploy: Render/Railway/Fly for zero-ops, or Kamal/Coolify on one VPS for fixed cost; preview deploy per PR; expand/contract migrations; OpenFeature-compatible flags (flagd file or Flagsmith).
- IaC: none for a pure PaaS app (platform config file in repo); OpenTofu once you have cloud resources beyond the PaaS.
- Capacity and cost: write the back-of-envelope numbers in the design doc; k6 smoke + average-load tests in CI before launch; budgets and usage limits set on every account on day one.

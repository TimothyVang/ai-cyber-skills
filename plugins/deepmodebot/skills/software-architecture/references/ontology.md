# Ontology for software projects and agent systems (2026)

Most projects need a shared vocabulary, not a formal ontology. Keep a glossary, bounded contexts and ADRs, and use one typed domain model (Pydantic or Zod). Map each term to exactly one code, DB and API name. That covers about 90% of cases [inference].
Use LinkML when one model has to produce three or more artifacts (Pydantic, SQL DDL, JSON Schema, SHACL, OWL, TypeScript). Use RDF + SHACL only when you exchange linked data with outside parties or need standard vocabularies such as schema.org or SKOS.
Use a property graph only when multi-hop traversal is the main query shape. On Postgres, start with Apache AGE. Check licenses before you pick: Neo4j CE is GPLv3, Memgraph is BSL, FalkorDB is SSPL, and Kuzu is archived.
For agents, the ontology is the typed tool surface. Define object types, link types and *actions* (validated, permissioned mutations), as Palantir Foundry does. Do not give agents raw write SQL or Cypher.
Do not treat LLM-built knowledge graphs (GraphRAG, LightRAG, Graphiti) as a source of truth. Give them a prescribed schema, keep provenance, and budget for indexing cost.

## How the three layers connect

| Layer | Artifact | Consumers | Failure if missing |
|---|---|---|---|
| 1. Vocabulary | `docs/GLOSSARY.md`, context map, ADRs | humans, agents reading the repo | the same concept gets 3 names across code, DB and API; agents invent a 4th |
| 2. Formal model | typed models (Pydantic/Zod), or LinkML YAML that generates them; optional RDF/SHACL or graph schema | compilers, validators, DB, other systems | schemas drift between languages and layers |
| 3. Agent ontology | tool/action schemas (JSON Schema), MCP servers, semantic-layer metrics | LLM agents | agents guess joins, write unsafe queries, hallucinate fields |

Rule: each layer is generated from or checked against the layer above it. A term absent from the glossary is not allowed in a schema; a field absent from the schema is not allowed in a tool [inference].

## 1. Domain vocabulary in the codebase

- **Ubiquitous Language** means a "common, rigorous language between developers and users" that is based on the domain model. It must be rigorous because "software doesn't cope well with ambiguity" ([Fowler, UbiquitousLanguage](https://martinfowler.com/bliki/UbiquitousLanguage.html)).
- **Bounded Context** is how DDD handles large models: divide them into contexts and be explicit about how the contexts relate. Polysemes such as "Customer" and "Product" mean different things in different contexts ([Fowler, BoundedContext](https://martinfowler.com/bliki/BoundedContext.html)). Do not force a single enterprise-wide model.
- **DDD Reference** (Evans) is free under CC BY 4.0. It is the canonical pattern summary to link instead of paraphrasing ([domainlanguage.com](https://www.domainlanguage.com/ddd/reference/)).
- **Context-map patterns** (Partnership, Shared Kernel, Customer/Supplier, Conformist, Anticorruption Layer, Open Host Service, Published Language) are summarized with Evans quotes in [ddd-crew/context-mapping](https://github.com/ddd-crew/context-mapping) (CC-BY-SA-4.0).
- **ADRs**: number them sequentially and never reuse a number. Mark reversed decisions "superseded" and keep them. Sections are Title, Context, Decision, Status, Consequences (list all consequences, not just the positive ones). Keep each ADR to 1-2 pages ([Nygard 2011](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)).
- **EventStorming** (Brandolini) is a workshop format. Big Picture, Process Modelling and Software Design variants discover domain events and expose language conflicts as "hot spots" ([eventstorming.com patterns](https://www.eventstorming.com/patterns/rush-to-the-goal); [ddd-crew glossary cheat sheet](https://github.com/ddd-crew/eventstorming-glossary-cheat-sheet)). Solo dev: run it alone on a whiteboard or in Markdown as an ordered list of past-tense events [inference].

### Glossary format that keeps names aligned

| Term | Context | Definition | Code | DB | API / event | Not to be confused with |
|---|---|---|---|---|---|---|
| Invoice | Billing | A request for payment issued to one Customer | `Invoice` | `invoice` | `/invoices`, `InvoiceIssued` | Quote (Sales), Receipt |
| Customer | Billing | Legal entity that pays invoices | `Customer` | `customer` | `/customers` | User (Identity), Account (Auth) |

Rules:
- One row per term per bounded context. If two contexts use the same word differently, it gets two rows [inference from Fowler above].
- Casing is mechanical (PascalCase type, snake_case table, kebab or plural path, past-tense event) and the root word never changes. A rename changes every column in one PR, and an ADR records the reason [inference].
- Enforce it cheaply: a CI `rg` check for banned synonyms listed in the glossary (for example `rg -n -w -i "client" src/billing`) [inference].
- The repo's `domain-modeling` skill covers writing GLOSSARY.md and ADRs. This file covers how they feed schemas and agents.

### Tools

| Tool | What | License | Latest release | Agent notes | Source |
|---|---|---|---|---|---|
| MADR | Markdown ADR template | MIT OR CC0-1.0 | 4.0.0 (2024-09-17); repo active 2026-11 | No release in 12+ months, but the template is stable. Copy it; do not install anything | [adr/madr](https://github.com/adr/madr) |
| adr-tools | Bash CLI for ADRs | see repo | 3.0.0 (2018-07-25) | **Unmaintained.** A plain numbered folder is enough | [npryce/adr-tools](https://github.com/npryce/adr-tools) |
| Context Mapper DSL | DSL for bounded contexts and context maps | Apache-2.0 | v6.12.0 (2024-08-30); commits 2026-10 | No release in 12+ months. Optional for teams of 1-3 | [ContextMapper](https://github.com/ContextMapper/context-mapper-dsl) |

## 2. Formal ontology and knowledge graphs

### Standards status (checked 2026-11-11)

| Standard | Status | Use for | Source |
|---|---|---|---|
| RDF 1.1 / RDF 1.2 | 1.1 is a Recommendation. RDF 1.2 Concepts was a Candidate Recommendation Snapshot on 2026-04-07 (adds triple terms) | data model of triples with IRIs | [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts) |
| OWL 2 | Recommendation (2012) | class axioms and inference under the open-world assumption | [OWL 2 Primer](https://www.w3.org/TR/owl2-primer/) |
| SKOS | Recommendation (2009) | taxonomies and thesauri (broader/narrower, labels) | [SKOS Reference](https://www.w3.org/TR/skos-reference/) |
| SHACL | 1.0 is a Recommendation (2017). SHACL 1.2 Core was a Working Draft on 2026-11-02 | **validating** RDF data under closed-world checks | [SHACL](https://www.w3.org/TR/shacl/); [SHACL 1.2 history](https://www.w3.org/standards/history/shacl12-core) |
| JSON-LD 1.1 | Recommendation (2020) | RDF as plain JSON, for web APIs and SEO | [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/) |
| schema.org | v30.1 (2026-09-15), Apache-2.0 repo | shared web vocabulary; Google recommends JSON-LD for structured data | [schemaorg/schemaorg](https://github.com/schemaorg/schemaorg); [Google structured data](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data) |
| GQL | ISO/IEC 39075:2024 (2024-04). Technical Corrigendum 1 published 2026 | standard property-graph query language | [ISO 39075](https://www.iso.org/standard/76120.html); [Cor 1:2026](https://www.iso.org/standard/93701.html) |
| openCypher | spec release 2024.3 (tagged 2026-03-20) | Cypher dialects used by Memgraph, FalkorDB, AGE and others | [opencypher/openCypher](https://github.com/opencypher/openCypher) |

Neo4j says Cypher "supports the majority of mandatory GQL features" and that users should expect "minimal differences" between Cypher and GQL ([Neo4j GQL conformance](https://neo4j.com/docs/cypher-manual/current/appendix/gql-conformance/)). Write Cypher today. GQL portability is a bonus, not a selection criterion [inference].

### When formal semantics pay off

| Worth it | Overkill |
|---|---|
| Exchanging data with other organizations that already publish RDF or SKOS (life sciences, government, libraries, Wikidata) | Single-app CRUD where Postgres plus typed models already enforce the shape |
| You need SEO rich results: emit schema.org JSON-LD from your existing models | Building an internal OWL ontology "for the AI" with no consumer that reasons over it |
| Many heterogeneous sources need merging under shared IRIs, with data-level validation (SHACL) | Validating API payloads: JSON Schema, Pydantic or Zod do it with less tooling |
| Controlled vocabularies with synonyms and hierarchy that domain experts curate (SKOS) | Hierarchies of under 50 terms: an enum plus a glossary is enough |

OWL makes the open-world assumption: a missing fact is unknown, not false ([OWL 2 Primer](https://www.w3.org/TR/owl2-primer/)). That is why OWL alone does not validate data, and SHACL exists ([SHACL](https://www.w3.org/TR/shacl/)).

### RDF and ontology tools

| Tool | What | License / free terms | Latest release | Agent notes | Source |
|---|---|---|---|---|---|
| Protege | Desktop OWL editor | BSD-style (Stanford) | 5.6.9 (2026-03-07) | Java GUI, so agents cannot drive it. Hand-edit Turtle instead | [protege](https://github.com/protegeproject/protege) |
| rdflib | Python RDF library, SPARQL, parsers | BSD-3-Clause | 7.6.0 (2026-02-13) | Default choice in Python. Good for generating JSON-LD/Turtle in tests | [RDFLib/rdflib](https://github.com/RDFLib/rdflib) |
| pySHACL | SHACL validator on rdflib | Apache-2.0 | v0.40.2 (2026-10-28) | CLI `pyshacl -s shapes.ttl data.ttl`, fits CI | [RDFLib/pySHACL](https://github.com/RDFLib/pySHACL) |
| Apache Jena + Fuseki | Java RDF framework, TDB2 store, SPARQL server | Apache-2.0 | 6.2.0 (tag 2026-07-27) | Fuseki is the default self-hosted SPARQL endpoint | [apache/jena](https://github.com/apache/jena) |
| Eclipse RDF4J | Java RDF framework (GraphDB is built on it) | BSD-3-Clause | 6.0.0 (2026-08-10) | Alternative to Jena | [rdf4j](https://github.com/eclipse-rdf4j/rdf4j) |
| Oxigraph | Rust SPARQL store, embeddable, with Python/JS bindings | Apache-2.0 (per GitHub) | v0.5.13 (2026-10-22) | Small and embeddable. Pre-1.0, so pin the version | [oxigraph](https://github.com/oxigraph/oxigraph) |
| QLever | Very fast SPARQL engine for huge datasets | Apache-2.0 | v0.6.0 (2026-08-13) | Only for read-heavy, Wikidata-scale data | [ad-freiburg/qlever](https://github.com/ad-freiburg/qlever) |
| GraphDB Free | RDF store with reasoning | **Proprietary, free license on request** (since 11.0). 2 concurrent queries, at most 5 repos, on-prem only | 11.x | Not OSS. Enterprise edition is paid per core | [GraphDB licensing](https://graphdb.ontotext.com/documentation/master/licensing.html) |
| TopBraid | SHACL API (OSS) plus EDG (paid). EDG Studio replaced TopBraid Composer | SHACL API Apache-2.0; EDG paid | SHACL API v1.5.0 (2026-03-23) | Composer is gone. The Java SHACL API remains a reference implementation | [TopQuadrant/shacl](https://github.com/TopQuadrant/shacl); [EDG Studio](https://www.topquadrant.com/doc/7.2/topbraid_edg_studio/index.html) |
| LinkML | YAML schema language that generates Pydantic, SQL DDL, SQLAlchemy, JSON Schema, SHACL, ShEx, OWL, JSON-LD context, TypeScript, Go, Rust, Java, GraphQL, protobuf, TypeQL and docs | Apache-2.0 | v1.12.1 (2026-10-13) | Best single-source-of-truth bridge between app types and semantic web. The `linkml-runtime` repo was folded into `linkml` on 2025-12-01 | [linkml](https://github.com/linkml/linkml); [generators](https://linkml.io/linkml/generators/index.html); [runtime note](https://github.com/linkml/linkml-runtime) |

### Property graph and typed-graph databases

| DB | Model / query | License | Latest | Status and agent notes | Source |
|---|---|---|---|---|---|
| Neo4j Community | property graph, Cypher | **GPLv3** (Enterprise is commercial) | 2026.10.2 (2026-10-29) | Mature. Calendar versioning; 5.26 is LTS. Running it as a separate server is common; embedding or distributing it brings GPL obligations [inference] | [neo4j/neo4j](https://github.com/neo4j/neo4j); [licensing](http://neo4j.com/licensing) |
| Memgraph | in-memory, Cypher | **BSL 1.1** with additional use grant. Bans DBaaS, distributing to third parties, and competing products. Changes to Apache-2.0 at the change date | v3.14.0 (2026-10-16) | Not OSI open source. Fine for internal use; read the grant before shipping it inside a product | [memgraph BSL](https://github.com/memgraph/memgraph/blob/master/licenses/BSL.txt) |
| FalkorDB | Redis-module graph, GraphBLAS, openCypher | **SSPLv1** | v6.0.4 (2026-11-05) | Not OSI open source. Offering it as a service triggers the SSPL | [FalkorDB license](https://docs.falkordb.com/license.html) |
| Kuzu | embedded columnar graph, Cypher | MIT | v0.11.3 (2025-10-10), final | **Archived 2025-10.** Press reports an Apple acquisition [unverified]. Graphiti marks it deprecated. Community fork: LadybugDB (MIT, v0.22.3, 2026-11-07) | [kuzudb/kuzu](https://github.com/kuzudb/kuzu); [The Register](https://www.theregister.com/2025/10/14/kuzudb_abandoned); [LadybugDB](https://github.com/LadybugDB/ladybug) |
| Apache AGE | Postgres extension, openCypher inside SQL | Apache-2.0 | PG18/v1.8.0-rc0 (2026-07-09). One release line per PG major; "-rc0" tags are marked non-prerelease | Best first graph for Postgres shops: one database, one backup. Check that your managed Postgres allows the extension | [apache/age](https://github.com/apache/age) |
| TypeDB | strongly typed entity-relation-attribute DB, TypeQL | MPL-2.0 (drivers Apache-2.0) | 3.15.0-rc0 (2026-11-10) | Schema-first with inheritance and n-ary relations, close to an ontology. Small ecosystem. LinkML has a TypeQL generator | [typedb/typedb](https://github.com/typedb/typedb) |
| TerminusDB | document + RDF graph with git-like versioning | Apache-2.0 | v12 (2025-12-08); v12.1.0-rc2 (2026-11-03) | Now stewarded by DFRNT. Niche; pick it for branch/merge of data | [terminusdb](https://github.com/terminusdb/terminusdb); [v12 post](https://terminusdb.org/blog/2025-12-08-terminusdb-12-release) |
| CozoDB | Datalog, relational-graph-vector | MPL-2.0 | v0.7.6 (2023-12-11) | **Unmaintained** (no commits since 2024-12) | [cozodb/cozo](https://github.com/cozodb/cozo) |

## 3. Ontologies for LLM agents

### Palantir Foundry Ontology as a design pattern (not a product recommendation)

- Foundry maps datasets and models to **object types** (an entity or event; an object is like a row), **properties** (columns), **link types** (relationships, like joins) and **action types**. An action type is a set of edits applied at once, plus side effects. Foundry also defines **functions** (code that takes objects as input), **interfaces** (polymorphism) and **roles** (permissions) ([Palantir core concepts](https://www.palantir.com/docs/foundry/ontology/core-concepts)).
- AIP agents get tools such as **Action**, which runs an ontology edit, automatically or after user confirmation, and **Object query**, which filters, aggregates and traverses only configured object types and properties ([AIP Agent Studio tools](https://www.palantir.com/docs/foundry/agent-studio/tools)). The OSDK generates typed TypeScript, Python and Java clients from the ontology ([OSDK](https://palantir.com/docs/foundry/ontology-sdk/overview)). Foundry itself is paid enterprise software.

Map the pattern onto your own stack [inference]:

| Palantir concept | Your stack | Exposed to agent as |
|---|---|---|
| Object type + properties | Pydantic/Zod model + table (or LinkML class) | read tool returning that model; JSON Schema in the tool description |
| Link type | foreign key / join table / graph edge | `get_<a>_<links>` read tool, never a free-form join |
| Action type | command function: validate input, check permission, mutate in one transaction, emit event, audit | one tool per action with a strict input schema; confirmation for destructive ones |
| Function | pure query or computation over typed objects | read-only tool |
| Interface | `Protocol` / TS interface shared by types | union-typed tool result |
| Roles | authz check inside each action | agent identity is scoped like a user's |

### Typed domain model = the agent's ontology

- The tool contract is JSON Schema. Claude tools take an `input_schema`, and `strict: true` guarantees calls match it ([Claude tool use](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview)). Strict mode takes a subset: objects need `additionalProperties: false`, and `minimum`, `maximum`, `minLength`, `maxLength` are rejected with HTTP 400 ([Claude JSON Schema limitations](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#json-schema-limitations)). OpenAI Structured Outputs follows a supplied JSON Schema but supports only **a subset** of the language ([OpenAI structured outputs](https://platform.openai.com/docs/guides/structured-outputs)).
- Generate that schema from the domain type; never hand-write it. Use Pydantic `BaseModel.model_json_schema()` ([Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/); v2.14.3, 2026-11-05, MIT) or Zod 4 `z.toJSONSchema()` ([Zod JSON Schema](https://zod.dev/json-schema); v4.6.7, 2026-10-12, MIT). For a strict Claude tool, pass the model through the Python SDK's `transform_schema()` (anthropic 2.8.0, 2026-11-10, Apache-2.0), which strips unsupported constraints into field descriptions and adds `additionalProperties: false` ([SDK transformation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#how-sdk-transformation-works)). Apply the same rewrite to a Zod schema before setting `strict: true` [inference].
- Put glossary definitions into field `description`s. They are the only ontology text the model sees at call time [inference].
- Parse model output back through the same type at the boundary (parse, don't validate), as in deepmodebot's type-system-discipline principle. That parse is also where constraints the provider stripped from the wire schema get enforced.

```python
from anthropic import transform_schema
from pydantic import BaseModel, Field

# Pydantic: one type drives DB mapping, API, and the agent tool schema
class IssueInvoice(BaseModel):
    """Action type: issue a draft invoice. Glossary: Invoice (Billing)."""
    invoice_id: str = Field(description="Invoice.id of a DRAFT invoice")
    due_in_days: int = Field(ge=1, le=90)

# model_json_schema() emits minimum/maximum and no additionalProperties: false, which
# strict mode rejects. transform_schema() moves the bounds into the description and closes objects.
tool = {"name": "issue_invoice", "description": IssueInvoice.__doc__,
        "input_schema": transform_schema(IssueInvoice), "strict": True}
args = IssueInvoice.model_validate(tool_use.input)  # enforces ge=1, le=90 again
```

### Semantic layers (governed metrics for agents)

dbt Labs' case: without a semantic layer, "AI emits raw SQL, guesses at joins, filters, time grains". Metrics "should be deterministic" ([dbt MetricFlow announcement](https://www.getdbt.com/blog/open-source-metricflow-governed-metrics)).

| Tool | What | License | Latest | Notes | Source |
|---|---|---|---|---|---|
| MetricFlow | metric definitions compiled to dialect SQL; engine behind the dbt Semantic Layer | **Apache-2.0 since 2025-10-14** (was BSL) | v0.213.0 (2026-09-10) | The hosted dbt Semantic Layer APIs are a dbt platform feature (paid tiers) [unverified] | [metricflow](https://github.com/dbt-labs/metricflow) |
| Cube Core | semantic layer server with SQL/REST/GraphQL APIs | Apache-2.0 (some parts MIT) | v1.8.22 (2026-11-11) | Self-host free. Cube Cloud is paid | [cube-js/cube](https://github.com/cube-js/cube) |
| Malloy | semantic modeling and query language over SQL databases | MIT | v0.0.437 (2026-10-30) | Pre-1.0 versioning; pin it | [malloydata/malloy](https://github.com/malloydata/malloy) |
| Apache Ossie (incubating) | vendor-neutral spec for exchanging semantic models; formerly OSI (Open Semantic Interchange) | Apache-2.0 | spec, no release yet | LinkML has `gen-ossie` | [apache/ossie](https://github.com/apache/ossie); [LinkML Ossie gen](https://linkml.io/linkml/generators/ossie.html) |

Use a semantic layer only once you have a warehouse and recurring metric questions. For an app DB, write named read functions (Palantir "functions") instead [inference].

### LLM-built knowledge graphs and agent memory

| Tool | What | License | Latest | Agent notes | Source |
|---|---|---|---|---|---|
| Microsoft GraphRAG | extracts entities/relations/claims, runs Leiden communities and community summaries; Global/Local/DRIFT/Basic search | MIT | v3.3.0 (2026-10-08) | README: "indexing can be an expensive operation... start small". Prompt tuning strongly recommended. Run `graphrag init --force` between minor versions | [graphrag](https://github.com/microsoft/graphrag); [docs](https://microsoft.github.io/graphrag/); [paper](https://arxiv.org/pdf/2404.16130) |
| LightRAG | lighter graph + vector RAG; storage on Neo4j, PostgreSQL, OpenSearch and others | MIT | v1.5.7 (tag 2026-09-02) | Cheaper incremental updates than GraphRAG [unverified] | [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) |
| Graphiti (Zep) | temporal context graph: bi-temporal edges, automatic fact invalidation, provenance; custom entity and edge types via Pydantic ("prescribed ontology") | Apache-2.0 | v0.31.2 (2026-10-20) | Backends: Neo4j, FalkorDB, Neptune (Kuzu deprecated). Needs structured-output LLMs. Reference MCP/REST servers have **no authentication** | [graphiti](https://github.com/getzep/graphiti); [Zep paper](https://arxiv.org/abs/2501.13956) |
| neo4j-graphrag-python | `SimpleKGPipeline` extracts into a declared schema (`node_types`, `relationship_types`, `patterns`) | Apache-2.0 (parts PSF) | 1.24.0 (2026-11-10) | Use the schema argument to stop entity-type sprawl | [neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python) |

### MCP servers exposing graphs and ontologies

| Server | Tools | License | Latest | Notes | Source |
|---|---|---|---|---|---|
| Neo4j official MCP | `get-schema`, `read-cypher` (rejects writes and admin), `write-cypher`, `list-gds-procedures` | GPLv3 | v2.1.1 (2026-11-11) | Neo4j docs on write-cypher: "LLM-generated queries can cause harm. Use only in development environments." Run with readonly mode | [neo4j/mcp](https://github.com/neo4j/mcp); [tools](https://neo4j.com/docs/mcp/current/tools) |
| Neo4j Labs mcp-neo4j | cypher, memory, data-modeling servers | MIT | mcp-neo4j-cypher v0.6.0 (2026-04-10) | Labs (community support) | [mcp-neo4j](https://github.com/neo4j-contrib/mcp-neo4j) |
| MCP reference memory server | local KG of entities (name, type, observations) and active-voice relations | MIT moving to Apache-2.0 | servers v2.4.0 (2026-11-11) | A toy-scale memory pattern. Not a domain ontology | [memory README](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) |
| Graphiti MCP | episodic and fact memory over Graphiti | Apache-2.0 | with Graphiti | Add auth before exposing it | [graphiti](https://github.com/getzep/graphiti) |

Prefer a domain MCP server whose tools are your action types over a generic query server [inference from Palantir tools + Neo4j caution].

## Decision table

| Situation | Approach | Why | Source |
|---|---|---|---|
| New app, 1 language, 1 DB | Plain typed model (Pydantic or Zod) + GLOSSARY.md + ADRs | Cheapest; types already enforce shape and export JSON Schema for tools | [Pydantic](https://docs.pydantic.dev/latest/concepts/json_schema/), [Zod](https://zod.dev/json-schema) |
| TS frontend + Python backend + SQL + agent tools must agree | LinkML as source; generate Pydantic, TypeScript, SQL DDL, JSON Schema | One model, many targets; removes drift | [LinkML generators](https://linkml.io/linkml/generators/index.html) |
| Publishing or consuming linked data, regulated or scientific data, shared vocabularies | RDF + SKOS + SHACL (generate shapes from LinkML or write them by hand); store in Jena/Fuseki or Oxigraph | Standards-based IRIs and closed-world validation | [SHACL](https://www.w3.org/TR/shacl/), [SKOS](https://www.w3.org/TR/skos-reference/) |
| SEO / rich results | schema.org JSON-LD emitted from existing models | No graph store needed | [Google structured data](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data) |
| Queries are mostly multi-hop paths (fraud rings, dependency graphs, permissions graphs) | Property graph: Apache AGE if you are on Postgres; else Neo4j CE (GPLv3) | Cypher expresses traversals that are painful in SQL | [AGE](https://github.com/apache/age), [Neo4j](https://github.com/neo4j/neo4j) |
| Rich typing: n-ary relations, inheritance, rule inference in the DB | TypeDB | Schema is an ontology | [TypeDB](https://github.com/typedb/typedb) |
| Agents answer metric questions over a warehouse | Semantic layer (MetricFlow, Cube or Malloy) | Deterministic metric SQL instead of guessed SQL | [dbt blog](https://www.getdbt.com/blog/open-source-metricflow-governed-metrics) |
| Agents mutate business state | Palantir-style ontology: object/link types + one tool per action with validation, permission and audit | Bounded, reviewable side effects | [Palantir](https://www.palantir.com/docs/foundry/ontology/core-concepts) |
| Q&A over a large unstructured corpus with global questions | GraphRAG (budget for it) or LightRAG | Community summaries answer corpus-wide questions | [GraphRAG](https://microsoft.github.io/graphrag/) |
| Long-lived agent memory with changing facts | Graphiti with prescribed Pydantic entity types | Bi-temporal invalidation keeps history | [Graphiti](https://github.com/getzep/graphiti) |

## Minimal example: one domain in LinkML

`schema/billing.yaml`:

```yaml
id: https://example.org/billing
name: billing
prefixes:
  linkml: https://w3id.org/linkml/
  schema: http://schema.org/
  billing: https://example.org/billing/
default_prefix: billing
default_range: string
imports: [linkml:types]
classes:
  Customer:
    class_uri: schema:Organization
    description: Legal entity that pays invoices (GLOSSARY Billing/Customer)
    attributes:
      id: {identifier: true}
      legal_name: {required: true, slot_uri: schema:legalName}
  Invoice:
    class_uri: schema:Invoice
    description: A request for payment issued to one Customer
    attributes:
      id: {identifier: true}
      customer: {range: Customer, required: true}
      status: {range: InvoiceStatus, required: true}
      total_cents: {range: integer, required: true, minimum_value: 0}
      issued_on: {range: date}
enums:
  InvoiceStatus:
    permissible_values: {draft: {}, issued: {}, paid: {}, void: {}}
```

Generate (CLI names from the [LinkML generator docs](https://linkml.io/linkml/generators/index.html)). Run them in CI and fail on diff, so generated files never drift:
```bash
linkml-lint schema/billing.yaml
gen-pydantic schema/billing.yaml > src/billing/models.py
gen-typescript schema/billing.yaml > web/src/billing.ts
gen-sqltables --dialect postgresql schema/billing.yaml > db/billing.sql
gen-json-schema schema/billing.yaml > schema/billing.schema.json   # feeds agent tool input_schema
gen-shacl schema/billing.yaml > schema/billing.shacl.ttl
gen-owl schema/billing.yaml > schema/billing.owl.ttl
gen-doc schema/billing.yaml -d docs/schema/                        # glossary-like docs site
```
Expected shape of the outputs (abbreviated and illustrative, not run here [inference]):
```python
class InvoiceStatus(str, Enum): draft = "draft"; issued = "issued"; paid = "paid"; void = "void"
class Invoice(ConfiguredBaseModel):
    id: str
    customer: str            # reference by Customer.id (identifier class, not inlined)
    status: InvoiceStatus
    total_cents: int = Field(..., ge=0)
    issued_on: Optional[date] = None
```
```sql
CREATE TABLE "Customer" (id TEXT NOT NULL, legal_name TEXT NOT NULL, PRIMARY KEY (id));
CREATE TABLE "Invoice" (id TEXT NOT NULL, customer TEXT NOT NULL, status VARCHAR(6) NOT NULL, total_cents INTEGER NOT NULL,
  issued_on DATE, PRIMARY KEY (id), FOREIGN KEY(customer) REFERENCES "Customer" (id));
```
```turtle
billing:Invoice a sh:NodeShape ; sh:closed true ; sh:targetClass schema:Invoice ;
  sh:property [ sh:path billing:status ; sh:in ("draft" "issued" "paid" "void") ; sh:maxCount 1 ; sh:minCount 1 ] .
```

Note: LinkML names SQL tables after classes. If your DB convention is snake_case, map names in a migration layer or adjust generator options. Record the choice in an ADR [inference].

## Traps for agents

- **Synonym drift.** The agent names a concept `Client` in the API, `customer` in SQL and `Account` in the UI. Fowler names this polyseme confusion as the reason bounded contexts exist ([BoundedContext](https://martinfowler.com/bliki/BoundedContext.html)). Check new names against GLOSSARY.md before you create one.
- **Ontology theater.** The agent proposes OWL, Protege or a graph DB for a CRUD app. Default to a typed model plus Postgres. Escalate only on a row in the decision table [inference].
- **OWL used as validation.** OWL's open-world assumption means missing values do not violate anything ([OWL 2 Primer](https://www.w3.org/TR/owl2-primer/)). Use SHACL, JSON Schema or Pydantic for validation.
- **Parallel hand-written schemas** (Pydantic + Zod + SQL + JSON Schema) drift silently. Pick one source (typed model or LinkML) and generate the rest [inference].
- **Raw write access for the agent.** Neo4j's own docs warn that LLM-generated write queries "can cause harm" ([Neo4j MCP tools](https://neo4j.com/docs/mcp/current/tools)). Expose action tools with confirmation, as AIP does ([Palantir tools](https://www.palantir.com/docs/foundry/agent-studio/tools)).
- **LLM-extracted graphs as truth.** Unconstrained extraction invents entity types and duplicates. Pass a schema (neo4j-graphrag `schema`, Graphiti custom types) and keep source provenance ([neo4j-graphrag](https://github.com/neo4j/neo4j-graphrag-python), [Graphiti](https://github.com/getzep/graphiti)).
- **Underestimating GraphRAG cost.** Microsoft warns that indexing is expensive. Start small and tune prompts ([GraphRAG README](https://github.com/microsoft/graphrag)).
- **Overwriting temporal facts.** Updating "current employer" in place loses history. Use valid-from/valid-to columns or a bi-temporal store ([Zep paper](https://arxiv.org/abs/2501.13956)).
- **License blindness.** Before you recommend a DB, check whether it is GPLv3 (Neo4j CE, Neo4j MCP), BSL (Memgraph), SSPL (FalkorDB) or archived (Kuzu). Run `gh api repos/<o>/<r>` for archived status and license ([Memgraph BSL](https://github.com/memgraph/memgraph/blob/master/licenses/BSL.txt), [FalkorDB](https://docs.falkordb.com/license.html), [Kuzu](https://github.com/kuzudb/kuzu)).
- **Schemas the provider rejects.** OpenAI Structured Outputs supports only a subset of JSON Schema. Test that the generated schema is accepted, not just valid ([OpenAI](https://platform.openai.com/docs/guides/structured-outputs)).
- **Unauthenticated memory servers.** Graphiti's reference MCP/REST servers ship without auth ([Graphiti README](https://github.com/getzep/graphiti)).
- **Agent-written metrics.** Ad-hoc SQL for "revenue" gives a different number every run. Route metric questions through named functions or a semantic layer ([dbt](https://www.getdbt.com/blog/open-source-metricflow-governed-metrics)).

## Default for a solo dev / small team

1. `docs/GLOSSARY.md` with the table format above, plus `docs/adr/NNNN-title.md` in MADR or Nygard format. Add a CI `rg` check for banned synonyms.
2. Postgres plus one typed domain model: Pydantic for Python backends, Zod for TS. It is the source of truth for API, DB mapping and agent tool `input_schema` (with `strict: true` where supported).
3. Agent surface = action tools (validate, authorize, one transaction, audit) plus read functions. No raw write SQL or Cypher, and read-only DB credentials for query tools.
4. Mixed TS/Python stack, or a need for SHACL/OWL/JSON-LD: switch the source of truth to LinkML (v1.12.x) and generate everything in CI.
5. Need graph traversal: Apache AGE on the same Postgres first; Neo4j CE (GPLv3, separate server) next. Avoid Kuzu (archived), and read Memgraph's BSL and FalkorDB's SSPL before you ship.
6. Need agent memory: Graphiti with declared Pydantic entity types on Neo4j or FalkorDB, behind your own auth. Need corpus Q&A: plain vector RAG first; GraphRAG or LightRAG only when global questions fail.
7. RDF only for schema.org JSON-LD (SEO) or external linked-data exchange: rdflib + pySHACL in Python, Oxigraph or Fuseki as the store.

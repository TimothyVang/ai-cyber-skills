# Authentication and authorization for AI agents: protocols, free/OSS tools, patterns (2026-11)

Strongest recommendations:
- Remote MCP servers: follow the MCP 2026-07-28 auth spec (OAuth 2.1 resource server, RFC 9728 metadata, RFC 8707 audience, PKCE, `iss` check). Prefer Client ID Metadata Documents; DCR is now deprecated. Never pass a client's token through to a downstream API ([MCP auth](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).
- Self-hosted and free: Keycloak (Apache-2.0) or Better Auth (MIT) as the authorization server; Pomerium (Apache-2.0) as an MCP gateway that holds upstream OAuth tokens so clients never see them ([Pomerium MCP](https://www.pomerium.com/docs/capabilities/mcp.md)).
- CI and cloud: no static cloud keys. Use GitHub OIDC federation to AWS/GCP/Azure with a `sub`-pinned trust policy ([GitHub](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws.md)).
- Agent acting for a user: delegated, scoped, short-lived tokens via RFC 8693 token exchange or a credential broker (Auth0 Token Vault, Composio, Arcade), with CIBA-style approval for risky actions.

Scope: protocols, identity providers, agent-identity products, and patterns for agents that call APIs, MCP servers, other agents, and clouds. Secret storage, `.env` handling, and leak scanning are in sibling notes. Release dates come from GitHub API on 2026-11-11.

## 1. Protocols and standards

| Standard | What it does for agents | Status (2026-11) | Agent-relevant notes | Source |
|---|---|---|---|---|
| MCP Authorization, rev 2026-07-28 | MCP server = OAuth 2.1 resource server; client = OAuth client; separate AS | Latest spec revision, tagged 2026-07-28 | HTTP transports SHOULD follow it; STDIO servers SHOULD NOT and instead "retrieve credentials from the environment" | [spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization), [tags](https://github.com/modelcontextprotocol/modelcontextprotocol/releases) |
| RFC 9728 Protected Resource Metadata | Server advertises its AS at `/.well-known/oauth-protected-resource` | RFC, Apr 2025 | MCP servers MUST implement; clients MUST use for AS discovery | [RFC 9728](https://www.rfc-editor.org/rfc/rfc9728) |
| RFC 8707 Resource Indicators | `resource=` binds a token to one server (audience) | RFC, Feb 2020 | MCP clients MUST send it in authorize and token requests; servers MUST check audience | [RFC 8707](https://www.rfc-editor.org/rfc/rfc8707) |
| PKCE (OAuth 2.1) | Stops code interception for public clients (CLIs, desktop agents) | OAuth 2.1 is draft-ietf-oauth-v2-1-17 (2026-10-31) | Required in the MCP flow diagram; MCP cites draft -13 | [OAuth 2.1](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/) |
| RFC 9207 `iss` response param | Defeats AS mix-up attacks | RFC, Mar 2022 | MCP 2026-07-28 makes clients record expected issuer and validate `iss` before redeeming the code | [RFC 9207](https://www.rfc-editor.org/rfc/rfc9207), [spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) |
| Client ID Metadata Documents (CIMD) | `client_id` is an HTTPS URL to a JSON metadata doc; no registration call | draft-ietf-oauth-client-id-metadata-document-03 (2026-11-02) | MCP: clients and AS SHOULD support CIMD; DCR "is deprecated and retained for backwards compatibility" | [draft](https://datatracker.ietf.org/doc/draft-ietf-oauth-client-id-metadata-document/), [spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) |
| RFC 7591 Dynamic Client Registration | Client self-registers via `POST /register` | RFC, Jul 2015 | MAY in MCP; open DCR lets any client register, so gate it | [RFC 7591](https://www.rfc-editor.org/rfc/rfc7591) |
| Token passthrough ban | MCP server must not accept or forward tokens not issued for it | Normative in MCP | "MCP servers MUST NOT accept or transit any other tokens"; see confused deputy | [spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization), [best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices.md) |
| MCP ext: OAuth Client Credentials | Machine-to-machine MCP with no user | Stable extension, 2026-07-28 | Pre-registered clients; `private_key_jwt` (RFC 7523) RECOMMENDED over client secret | [ext-auth](https://github.com/modelcontextprotocol/ext-auth) |
| MCP ext: Enterprise-Managed Authorization | SSO identity assertion -> MCP access token, no per-server consent | Stable extension, 2026-07-28 | Profile of ID-JAG (below): token exchange at IdP + RFC 7523 grant at MCP AS | [ext-auth](https://github.com/modelcontextprotocol/ext-auth) |
| RFC 8693 Token Exchange | Swap a user token for a narrower token; `actor_token` records the agent (`act` claim) | RFC, Jan 2020 | Core on-behalf-of primitive; supported by Keycloak, Zitadel, authentik, Auth0 | [RFC 8693](https://www.rfc-editor.org/rfc/rfc8693) |
| ID-JAG / Cross App Access (XAA) | App uses an SSO identity assertion to get a token for a third-party API via the IdP | draft-ietf-oauth-identity-assertion-authz-grant-06 (2026-10-31) | Builds on draft-ietf-oauth-identity-chaining-17; Okta ships it as XAA | [draft](https://datatracker.ietf.org/doc/draft-ietf-oauth-identity-assertion-authz-grant/) |
| RFC 9449 DPoP | Sender-constrains tokens to a client key, so a stolen token is useless alone | RFC, Sep 2023 | Good fit for long-running agents holding refresh tokens; Keycloak has a DPoP guide | [RFC 9449](https://www.rfc-editor.org/rfc/rfc9449) |
| RFC 8628 Device Authorization Grant | User approves on a second device; agent polls | RFC, Aug 2019 | Best login flow for headless agents and SSH sessions; offered by Clerk, authentik, Better Auth | [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628) |
| OpenID CIBA Core 1.0 | Backchannel request; user approves on phone; client polls or is pinged | Final, Sep 2021 | Human approval of a sensitive agent action; Auth0 "Asynchronous Authorization" uses it | [CIBA](https://openid.net/specs/openid-client-initiated-backchannel-authentication-core-1_0.html), [Auth0](https://auth0.com/ai/docs/intro/asynchronous-authorization) |
| Transaction Tokens | Short-lived, call-chain-scoped tokens inside a trust domain | draft-ietf-oauth-transaction-tokens-11 (2026-08-21) | Agent extension: draft-oauth-transaction-tokens-for-agents-06 (individual) adds `act` for the agent | [draft](https://datatracker.ietf.org/doc/draft-ietf-oauth-transaction-tokens/), [agents](https://datatracker.ietf.org/doc/draft-oauth-transaction-tokens-for-agents/) |
| AI agent auth drafts | Best-practice framing: WIMSE identity + OAuth for agents | draft-klrc-aiagent-auth-03 (2026-09-09), individual | Reuses existing standards rather than new protocol; on-behalf-of draft (draft-oauth-ai-agents-on-behalf-of-user-02) is expired | [klrc](https://datatracker.ietf.org/doc/draft-klrc-aiagent-auth/), [OBO](https://datatracker.ietf.org/doc/draft-oauth-ai-agents-on-behalf-of-user/) |
| SPIFFE / WIMSE | Attested workload identity (X.509-SVID, JWT-SVID, WIT-SVID) instead of shared secrets | SPIFFE specs; draft-ietf-wimse-arch-08 | Google Agent Identity issues SPIFFE IDs per agent | [SPIFFE](https://spiffe.io/docs/latest/spire-about/spire-concepts/), [WIMSE](https://datatracker.ietf.org/doc/draft-ietf-wimse-arch/) |
| A2A auth | Agent Card `securitySchemes`; creds obtained out-of-band; sent in headers on every request | A2A v1.0.1 (2026-05-28), Apache-2.0 | `TASK_STATE_AUTH_REQUIRED` lets an agent ask the client for a credential or human approval mid-task | [spec](https://a2a-protocol.org/latest/specification/), [repo](https://github.com/a2aproject/A2A) |
| CI OIDC federation | CI job gets a signed JWT, trades it for short-lived cloud creds | GA on GitHub Actions | Needs `permissions: id-token: write`; pin `sub` in the trust policy | [GitHub OIDC ref](https://docs.github.com/en/actions/reference/security/oidc.md) |

Minimal MCP challenge a server returns (from the spec):

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource", scope="files:read"
```

On-behalf-of token exchange per RFC 8693 (agent backend, never the model, makes this call). The tokens and client secret reach curl as a config file on stdin (`-K -`); `printf` is a shell builtin, so none of them appear in the process list:

```sh
printf '%s\n' \
  "user = \"$CLIENT_ID:$CLIENT_SECRET\"" \
  "data-urlencode = \"subject_token=$USER_ACCESS_TOKEN\"" \
  "data-urlencode = \"actor_token=$AGENT_TOKEN\"" |
curl -s -K - https://as.example.com/token \
  -d grant_type=urn:ietf:params:oauth:grant-type:token-exchange \
  -d subject_token_type=urn:ietf:params:oauth:token-type:access_token \
  -d actor_token_type=urn:ietf:params:oauth:token-type:jwt \
  -d resource=https://api.example.com -d scope="calendar:read"
```

Rules:
- The MCP server validates audience (RFC 8707 / RFC 9068 `aud`) and returns 401 or 403 with `insufficient_scope`; clients union scopes on step-up and cap retries ([spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).
- Tokens go only in the `Authorization: Bearer` header, never in query strings (MUST in the spec).
- Ask for the challenged scopes, not `scopes_supported`; servers SHOULD NOT list `offline_access` ([spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).

## 2. Open-source identity providers and gateways

| Tool | What it does | License (checked LICENSE) | Latest release | Agent / MCP notes | Source |
|---|---|---|---|---|---|
| Keycloak | Full OIDC/OAuth AS, SSO, token exchange | Apache-2.0 | 26.8.2, 2026-11-05 | Official MCP guide. DCR supported; CIMD and RFC 8707 are experimental (`--features=cimd,resource-indicators`); 26.7 added ID-JAG and Token Exchange Delegation (both experimental) | [MCP guide](https://www.keycloak.org/securing-apps/mcp-authz-server), [notes](https://www.keycloak.org/docs/latest/release_notes/index.html), [repo](https://github.com/keycloak/keycloak) |
| Better Auth | TypeScript auth library; OAuth 2.1 provider plugin | MIT | v1.7.21, 2026-11-11 | OAuth Provider plugin: DCR, CIMD, RFC 8707 resources, `iss` in responses; `mcp()` plugin protects an MCP server; device authorization plugin | [OAuth provider](https://better-auth.com/llms.txt/docs/plugins/oauth-provider.md), [repo](https://github.com/better-auth/better-auth) |
| Pomerium | Identity-aware proxy and MCP gateway | Apache-2.0 | v0.34.1, 2026-11-11 | Fronts MCP servers; acquires, caches, refreshes upstream OAuth tokens and injects them so "clients never see upstream credentials"; `mcp_tool` policy denies tools by name; MCP and CIMD code live in the OSS repo (`internal/mcp`) | [docs](https://www.pomerium.com/docs/capabilities/mcp.md), [upstream OAuth](https://www.pomerium.com/docs/capabilities/mcp/mcp-upstream-oauth.md), [repo](https://github.com/pomerium/pomerium) |
| Zitadel | Multi-tenant IdP, OIDC/OAuth, SAML | AGPL-3.0-only (proto/docs Apache-2.0; login app and client packages MIT) | v4.20.2, 2026-11-09 | RFC 8693 token exchange for impersonation and delegation; AGPL network-use obligations if you modify it | [token exchange](https://zitadel.com/docs/guides/integrate/token-exchange), [LICENSING.md](https://github.com/zitadel/zitadel/blob/main/LICENSING.md) |
| authentik | IdP plus proxy outpost | MIT for core; `authentik/enterprise/` under separate license | 2026.8.5, 2026-10-21 | 2026.8 added DCR, on-behalf-of with `act` claim, provider token exchange, key-bound ID tokens; whether DCR is enterprise-only is [unverified] | [2026.8 notes](https://docs.goauthentik.io/releases/2026.8), [LICENSE](https://github.com/goauthentik/authentik/blob/main/LICENSE) |
| Logto | IdP with SaaS and self-host | MPL-2.0 | v1.46.0, 2026-11-05 | MCP guides; "dynamic app" lets any agent connect without pre-registration; Cloud Free: 50,000 MAU, 1 M2M app, 3 API resources | [MCP 3rd-party](https://docs.logto.io/use-cases/ai/mcp-server-enable-third-party-ai-agent-access), [pricing](https://logto.io/pricing), [repo](https://github.com/logto-io/logto) |
| Ory Hydra / Kratos / Oathkeeper | Headless OAuth2/OIDC server, identity, proxy | Apache-2.0 | OSS v26.2.0, 2026-03-20 (all three) | MCP guide uses DCR + resource URL as audience. Ory Enterprise License (OEL) builds ship faster (Hydra OEL v26.4.12, 2026-11-05) and carry CVE-patch SLAs; OSS gets fewer releases | [MCP guide](https://www.ory.com/docs/guides/mcp/hydra-oauth), [README](https://github.com/ory/hydra), [OEL changelog](https://changelog.ory.com/announcements/ann_TJsQYiQNQcPmH) |
| Authelia | SSO/2FA forward-auth portal | Apache-2.0 | v4.39.28, 2026-09-17 | OIDC Provider role is still an "open beta"; fine for homelab SSO in front of agent UIs, weaker fit as MCP AS [inference] | [OIDC docs](https://www.authelia.com/configuration/identity-providers/openid-connect/provider/index.md), [repo](https://github.com/authelia/authelia) |
| SuperTokens | Auth library + core | Apache-2.0 for core; `ee/` separate license | v12.5.0, 2026-11-06 | MCP auth plugin exists but docs say "This feature is only available to paid users" | [MCP docs](http://supertokens.com/docs/authentication/ai-authentication), [LICENSE.md](https://github.com/supertokens/supertokens-core/blob/master/LICENSE.md) |
| oauth2-proxy | Reverse proxy that adds OIDC login | MIT | v7.15.6, 2026-11-05 | Browser SSO in front of internal agent dashboards; it does not implement MCP RFC 9728 discovery [inference] | [repo](https://github.com/oauth2-proxy/oauth2-proxy) |
| Cloudflare workers-oauth-provider | OAuth 2.1 AS library for Workers and remote MCP | MIT | v1.2.4, 2026-10-22 | Pre-registered, CIMD, DCR, PKCE; "Tokens, codes and secrets are stored only as hashes"; CIMD needs `global_fetch_strictly_public` (SSRF guard). Workers Free: 100,000 requests/day | [README](https://github.com/cloudflare/workers-oauth-provider), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) |
| step-ca | Private CA for short-lived X.509/SSH certs | Apache-2.0 | v0.30.2, 2026-03-23 | Short-lived certs with passive revocation; OIDC, ACME, cloud-instance-identity provisioners; good for mTLS between agents and services | [README](https://github.com/smallstep/certificates) |
| SPIRE | SPIFFE runtime: node and workload attestation, SVID issuance | Apache-2.0 | v1.16.0, 2026-11-05 | Gives each agent workload an attested identity with no stored secret | [concepts](https://spiffe.io/docs/latest/spire-about/spire-concepts/), [repo](https://github.com/spiffe/spire) |
| Teleport | Access proxy for SSH, k8s, DBs, apps, MCP | Source AGPL-3.0; downloadable Community Edition binaries under a modified license | v18.10.0, 2026-07-09 | MCP access for stdio, SSE, streamable-HTTP servers. Community Edition binaries are "AVAILABLE ONLY TO ORGANIZATIONS THAT HAVE LESS THAN ONE HUNDRED (100) EMPLOYEES AND LESS THAN TEN MILLION DOLLARS" revenue: not OSI open source | [MCP docs](https://goteleport.com/docs/enroll-resources/mcp-access/), [CE license](https://github.com/gravitational/teleport/blob/master/build.assets/LICENSE-community) |

Keycloak as a local MCP authorization server (dev mode; flags from the Keycloak MCP guide):

```sh
bin/kc.sh start-dev --features=cimd,resource-indicators
```

Pomerium route that gives an LLM client GitHub MCP without exposing the GitHub token, and blocks admin tools (from Pomerium docs):

```yaml
routes:
  - from: https://github.your-domain.com
    to: http://github-mcp.int:8080/mcp
    mcp:
      server:
        upstream_oauth2:
          client_id: xxxx
          client_secret: yyyy   # load from a secret store, not the repo
          scopes: ['read:user', 'user:email']
          endpoint: {auth_url: 'https://github.com/login/oauth/authorize', token_url: 'https://github.com/login/oauth/access_token'}
    policy:
      allow: {and: [{domain: {is: company.com}}]}
      deny:  {and: [{mcp_tool: {starts_with: 'admin_'}}]}
```

## 3. Commercial agent-identity products with free tiers

| Product | What it does for agents | Free terms (vendor page, 2026-11) | Agent-relevant notes | Source |
|---|---|---|---|---|
| Auth0 for AI Agents (Token Vault, Async Authorization) | Login, Token Vault for third-party tokens, CIBA approval, FGA for RAG | Free: up to 25,000 MAU, "Secure Agentic AI workflows"; feature table lists Token Vault "2" on Free (unit not stated, likely connections [inference]); CIBA "Not available" on Free; paid AI Agents add-on is +50% of base price | Agent exchanges an Auth0 token for a scoped provider token; provider refresh tokens stay in Auth0 | [pricing](https://auth0.com/pricing.md), [Token Vault](https://auth0.com/ai/docs/intro/call-third-party-apis-on-users-behalf) |
| WorkOS AuthKit (MCP Auth / Connect) | Hosted AS for MCP servers; M2M; user mgmt | AuthKit free up to 1 million users, then $2,500 per extra 1M | CIMD supported; DCR can be enabled for older clients; inclusion of MCP Auth in the free allowance is [unverified] | [pricing](https://workos.com/pricing), [MCP docs](https://workos.com/docs/authkit/mcp.md) |
| Descope (Agentic Identity Hub, Inbound/Outbound Apps) | MCP/API resource protection, consent, outbound token vault | Free Forever: 7,500 MAU, 10 tenants, 3 SSO, 10,000 M2M exchanges, 2,000 monthly active consents, 2,000 monthly active tokens; no overages, upgrade required | Token exchange and client-credentials exchanges count as M2M exchanges | [pricing](https://www.descope.com/pricing), [docs](https://docs.descope.com/agentic-identity-hub) |
| Stytch Connected Apps | Turns your app into an OAuth AS for MCP and agents | "Always free: 10,000 monthly active users and AI agents", 5 SSO/SCIM, 1,000 M2M tokens | CIMD support since 2025-10-17 | [pricing](https://stytch.com/pricing), [MCP docs](https://stytch.com/docs/connected-apps/guides/mcp-auth-overview), [CIMD](https://changelog.stytch.com/announcements/client-id-metadata-documents-cimd-1) |
| Clerk | Auth + OAuth server for MCP | Hobby: 50,000 MRU per app, 3 dashboard seats, fixed 7-day sessions, capped API keys/M2M tokens | OAuth server supports CIMD, DCR, PKCE, device grant; MCP server guides | [pricing](https://clerk.com/pricing), [OAuth](https://clerk.com/docs/guides/configure/auth-strategies/oauth/how-clerk-implements-oauth) |
| Keycard | Runtime authorization and identity for agents | Starter: 5,000 transactions/mo hard cap, unlimited users, agents, apps | Policy (RBAC/ABAC/ReBAC) per agent action | [pricing](https://www.keycard.ai/pricing/) |
| Arcade.dev | Tool runtime that handles OAuth and user tokens for agent tools | Free: 2,000 tool calls/month; Team $25/mo + $0.01/call | `arcade-mcp` framework is MIT (no tagged releases; last commit 2026-11-10) | [pricing](https://www.arcade.dev/pricing), [docs](https://docs.arcade.dev/en/home/auth/how-arcade-helps), [repo](https://github.com/ArcadeAI/arcade-mcp) |
| Composio | Managed auth + 1,700+ toolkits | Hobby: 100,000 tool calls/mo (up to 20,000 on Composio-managed apps), unlimited connected accounts (first 1,000 free on managed apps), 50,000 triggers, 3 members | "Provider credentials are not required in prompts, tool arguments, or model context"; SDK MIT (`@composio/cli@0.6.0`, 2026-11-01) | [pricing](https://composio.dev/pricing.md), [token custody](http://docs.composio.dev/docs/security/token-custody), [repo](https://github.com/ComposioHQ/composio) |
| Aembit | Workload/agent IAM, MCP identity gateway | Agentic AI Starter: 3 AI agents, 1 MCP identity gateway, 5 MCP authorization policies, 24 h logs; Workloads Starter: 10 workloads, 10 policies | Secretless access via attested identity | [pricing](https://aembit.io/pricing) |
| Cloudflare Access + MCP server portals | Zero-trust gateway in front of MCP servers | Zero Trust Free: up to 50 users | Portal applies IdP and MFA policy to MCP; needs a domain on Cloudflare | [plans](https://www.cloudflare.com/plans/sase-zero-trust.md), [MCP portals](https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/) |
| AWS Bedrock AgentCore Identity | Agent identity directory, inbound JWT, outbound OAuth/API-key vault | No extra charge when used via AgentCore Runtime or Gateway; otherwise billed per successful token/API-key request (AWS account, not free) | Supports on-behalf-of token exchange | [pricing](https://aws.amazon.com/bedrock/agentcore/pricing/), [features](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/key-features-and-benefits.html) |
| Google Agent Identity | SPIFFE ID + X.509 per agent; auth manager for 3LO | Paid GCP; launch stage [unverified] | Google Cloud access tokens bound to the agent's certificate; logs show agent and user | [overview](https://docs.cloud.google.com/iam/docs/agent-identity-overview) |
| Microsoft Entra Agent ID | Agent identities from blueprints | "Available for all Microsoft Entra customers"; Agent 365 is licensed per user | Paid tenant context; enterprise only | [licensing](https://learn.microsoft.com/en-us/entra/fundamentals/licensing) |
| Okta Cross App Access | ID-JAG issuer for agent-to-app and MCP | Paid; "Cross App Access support for MCP Servers is GA in Preview" (2026-10-28) | Admin-approved connections replace per-user consent | [concept](https://developer.okta.com/docs/concepts/xaa/), [notes](https://developer.okta.com/docs/release-notes/2026-okta-identity-engine/) |

## 4. CI and cloud: workload identity federation instead of keys

| Action | Purpose | License | Latest release | Note | Source |
|---|---|---|---|---|---|
| aws-actions/configure-aws-credentials | GitHub OIDC -> AWS STS role | MIT | v6.3.0, 2026-09-15 | Audience `sts.amazonaws.com` | [repo](https://github.com/aws-actions/configure-aws-credentials) |
| google-github-actions/auth | GitHub OIDC -> GCP Workload Identity Federation | Apache-2.0 | v3.0.0, 2025-08-28 | No release in 14 months (commits through 2026-07); still the documented path, watch it | [repo](https://github.com/google-github-actions/auth) |
| Azure/login | GitHub OIDC -> Entra federated credential | MIT | v3.1.0, 2026-09-10 | No client secret needed with federated credentials | [repo](https://github.com/Azure/login) |

```yaml
permissions:
  id-token: write   # required to request the OIDC JWT
  contents: read
steps:
  - uses: aws-actions/configure-aws-credentials@<pinned-sha>
    with: {role-to-assume: arn:aws:iam::123456789012:role/ci-deploy, aws-region: us-east-1}
```

Trust-policy rule: AWS IAM recommends evaluating `token.actions.githubusercontent.com:sub` so only the intended repo/branch/environment can assume the role; repos with immutable subject claims put owner and repo IDs in `sub` ([GitHub](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws.md), [OIDC reference](https://docs.github.com/en/actions/reference/security/oidc.md)). Example condition: `"StringEquals": {"token.actions.githubusercontent.com:sub": "repo:ORG/REPO:environment:prod", "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"}`.

## 5. Patterns

1. Agent acts on behalf of a user (delegation). User consents once (auth code + PKCE, or device flow for headless agents). The agent backend holds the refresh token; each call uses a short-lived, audience-bound access token. Use RFC 8693 with `actor_token` so logs carry both user and agent (`act` claim) ([RFC 8693](https://www.rfc-editor.org/rfc/rfc8693), [authentik OBO](https://docs.goauthentik.io/releases/2026.8)).
2. Agent as its own identity (machine). Use client credentials with `private_key_jwt`, not a shared secret ([MCP client-credentials ext](https://github.com/modelcontextprotocol/ext-auth)), or attested workload identity (SPIRE, cloud OIDC, Google Agent Identity), so there is no long-lived secret to steal.
3. Credential broker keeps third-party tokens out of the model. The LLM sees tool names and results; a broker (Auth0 Token Vault, Composio, Arcade, Pomerium upstream OAuth, Descope outbound apps) stores provider tokens and injects them at execution ([Composio](http://docs.composio.dev/docs/security/token-custody), [Pomerium](https://www.pomerium.com/docs/capabilities/mcp.md)). The broker API key becomes the crown jewel: keep it server-side.
4. Gateway in front of tools. An identity-aware proxy (Pomerium, Cloudflare Access, Teleport) authenticates the human or agent, then filters per tool (`mcp_tool` deny rules) before the MCP server sees the call.
5. Human approval for sensitive actions. CIBA (Auth0 Async Authorization), A2A `TASK_STATE_AUTH_REQUIRED`, or MCP step-up scopes (403 `insufficient_scope`) force a fresh human decision for writes, payments, deletes ([A2A](https://a2a-protocol.org/latest/specification/), [CIBA](https://openid.net/specs/openid-client-initiated-backchannel-authentication-core-1_0.html)).
6. Enterprise SSO for agents. ID-JAG / XAA or MCP Enterprise-Managed Authorization lets an admin pre-approve which MCP servers a user's agent may reach, with no per-server consent screen ([ext-auth](https://github.com/modelcontextprotocol/ext-auth)).

Rules for agent builders:
- Scope per task and per resource; request challenged scopes only; prefer minutes-long access tokens plus server-held refresh tokens [inference].
- Never put an access or refresh token in the prompt, a tool argument, a log line, or a URL.
- Bind tokens: audience (RFC 8707) always; DPoP or mTLS when the agent runs long or on untrusted hosts.
- Separate identities: one client per agent deployment, so you can revoke one agent without logging out the user [inference].

## 6. Decision table: situation -> recommended free option

| Situation | Free option | Why | Source |
|---|---|---|---|
| Protect your own remote MCP server, self-hosted | Keycloak (Apache-2.0) with `cimd,resource-indicators` features, or Better Auth OAuth Provider (MIT) if your app is TypeScript | Spec-aligned AS with CIMD + RFC 8707; no MAU caps | [Keycloak](https://www.keycloak.org/securing-apps/mcp-authz-server), [Better Auth](https://better-auth.com/llms.txt/docs/plugins/oauth-provider.md) |
| Protect a remote MCP server on serverless | `workers-oauth-provider` (MIT) on Workers Free (100,000 req/day) | Hashes tokens at rest; CIMD with SSRF guard flag | [README](https://github.com/cloudflare/workers-oauth-provider) |
| Hosted AS, zero ops, many users | WorkOS AuthKit (free to 1M users) or Stytch (10,000 MAU + agents) | CIMD support; large free allowance | [WorkOS](https://workos.com/pricing), [Stytch](https://stytch.com/pricing) |
| Give agents access to internal MCP servers without handing out upstream tokens | Pomerium OSS (Apache-2.0) | Upstream OAuth held by gateway; per-tool deny policy | [Pomerium](https://www.pomerium.com/docs/capabilities/mcp/mcp-upstream-oauth.md) |
| Small team, SaaS gateway with MFA in front of MCP | Cloudflare Zero Trust Free (50 users) + MCP portals | IdP + MFA policy, no servers to run | [plans](https://www.cloudflare.com/plans/sase-zero-trust.md) |
| Agent calls Gmail/GitHub/Slack for end users | Composio Hobby (100,000 calls) or Auth0 Free (25,000 MAU, Token Vault) | Broker stores provider tokens outside model context | [Composio](https://composio.dev/pricing.md), [Auth0](https://auth0.com/pricing.md) |
| CI job or agent needs AWS/GCP/Azure | GitHub OIDC + official login actions | No stored cloud keys; creds expire with the job | [GitHub OIDC](https://docs.github.com/en/actions/reference/security/oidc.md) |
| Service-to-service or agent-to-agent identity in your infra | SPIRE (Apache-2.0) or step-ca (Apache-2.0) short-lived certs | Attested or short-lived identity, mTLS | [SPIRE](https://github.com/spiffe/spire), [step-ca](https://github.com/smallstep/certificates) |
| Headless agent needs a user login | Device grant (RFC 8628) from Keycloak, authentik, Clerk, or Better Auth | User approves on phone; agent never sees password | [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628) |
| Human must approve a risky action | Step-up via MCP `insufficient_scope` + your IdP; CIBA needs Auth0 paid or a self-hosted CIBA AS [inference] | Fresh consent per sensitive scope | [spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization), [Auth0 pricing](https://auth0.com/pricing.md) |
| Need multi-tenant IdP and accept AGPL | Zitadel (AGPL-3.0-only) | RFC 8693 token exchange, orgs | [Zitadel](https://zitadel.com/docs/guides/integrate/token-exchange) |
| Access proxy for SSH/k8s/DB plus MCP, under 100 staff and $10M revenue | Teleport Community Edition | Free only under those caps; not OSS binaries | [CE license](https://github.com/gravitational/teleport/blob/master/build.assets/LICENSE-community) |

## Threats and failure modes

- Token passthrough and confused deputy: an MCP server that accepts tokens issued for another audience and forwards them lets attackers bypass rate limits, audit, and consent; static-client-ID OAuth proxies can skip user consent unless they keep per-client consent ([MCP best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices.md)).
- Malicious server metadata attacks the client: CVE-2025-6514 (CVSS 9.6) let a crafted `authorization_endpoint` from an untrusted MCP server run OS commands via `mcp-remote` ([CVE record](https://www.cve.org/CVERecord?id=CVE-2025-6514), [GHSA](https://github.com/advisories/GHSA-6xpm-ggf7-wc3p)). Only connect agents to MCP servers you trust and keep clients patched.
- SSRF via discovery and CIMD: the AS fetches client-supplied URLs; MCP best practices has an SSRF section, and Cloudflare requires `global_fetch_strictly_public` before accepting CIMD ([best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices.md), [README](https://github.com/cloudflare/workers-oauth-provider)).
- Mix-up attacks: without RFC 9207 `iss` checks a client can send its code to the wrong AS; MCP 2026-07-28 now requires recording and checking the issuer ([spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).
- Identity and privilege abuse: OWASP Agentic Top 10 2026 lists ASI03 "Identity and Privilege Abuse" (delegation chains, inherited roles, cached credentials) ([OWASP](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)). Prompt injection turns over-scoped tokens into data exfiltration [inference].
- Open registration: unrestricted DCR lets anyone mint clients; the spec deprecated DCR in favor of CIMD; gate or disable DCR in production ([spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).
- STDIO servers read credentials from the environment by spec, so any agent with shell access can read them; keep long-lived keys out of the agent's env and use brokers or short-lived tokens instead ([spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)) [inference on risk].
- Refresh-token theft from client storage: the spec says clients MUST keep refresh tokens confidential in transit and storage; DPoP or key-bound tokens limit replay ([spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization), [RFC 9449](https://www.rfc-editor.org/rfc/rfc9449)).
- Over-broad CI trust policies: missing `sub` condition lets other repos or branches assume your cloud role ([GitHub](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws.md)).
- Broker keys and shared OAuth apps: a Composio API key "is still a secret with permission to act on connected accounts"; Composio-managed apps are shared OAuth apps that "work in production but are not built for production scale" and share provider rate limits, so register your own OAuth app ([token custody](http://docs.composio.dev/docs/security/token-custody), [pricing](https://composio.dev/pricing.md)).
- Licensing traps: Teleport CE binaries, SuperTokens MCP plugin (paid), Ory OEL-only features and SLA-backed CVE releases, authentik `enterprise/` code, Zitadel AGPL. "Free to download" is not "free to use at your size" ([Teleport](https://github.com/gravitational/teleport/blob/master/build.assets/LICENSE-community), [SuperTokens](http://supertokens.com/docs/authentication/ai-authentication), [Ory](https://github.com/ory/hydra)).

## Recommendation for a solo dev / small team, all free

1. Local coding agents (Claude Code, Codex, Cursor): use OAuth-based MCP servers where offered, so tokens live in the client's store, not in `.env`; for stdio servers, pass short-lived tokens, not account passwords [inference].
2. Your own remote MCP server: Better Auth OAuth Provider (TS apps) or Keycloak (anything else); enable CIMD and resource indicators; validate `aud`; never forward the inbound token; return 403 `insufficient_scope` for write tools ([spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).
3. If you would rather not run an AS: WorkOS AuthKit or Stytch free tiers; or `workers-oauth-provider` on Workers Free.
4. Agents calling third-party SaaS for you or your users: Composio Hobby or Auth0 Free Token Vault, so provider tokens stay outside the model context.
5. Internal tools behind one gate: Pomerium OSS with upstream OAuth and `mcp_tool` deny rules, or Cloudflare Zero Trust Free (50 users).
6. CI and deploy agents: GitHub OIDC to AWS/GCP/Azure with `sub` pinned to repo + environment; delete static cloud keys.
7. Service identity at home-lab scale: step-ca short-lived certs; move to SPIRE when you run several hosts or k8s.
8. Approval: require a human step-up (new consent or a separate approval tool) for destructive scopes; keep agent and user identities separate in logs via the `act` claim.

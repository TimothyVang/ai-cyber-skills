# Azure Security and DevSecOps

Read when designing, reviewing, debugging, or securing Azure deployments: management groups and landing zones, Entra ID identities, RBAC, Azure Policy, Defender for Cloud, Key Vault and Storage, Private Endpoints and DNS, logging and Sentinel, GitHub Actions or Azure Pipelines federation to Azure, Bicep/Terraform validation, or AKS. Facts as of 2026-11-11.
Full report: https://github.com/TimothyVang/cloud-devsecops/blob/main/research/azure-devsecops.md

## Recent changes that break assumptions

- **GitHub OIDC `sub` uses immutable IDs** for repos created, renamed, or transferred after 2026-07-15: `repo:ORG@OWNER_ID/REPO@REPO_ID:...`. Name-based federated credentials silently stop matching after a rename or transfer ([GitHub OIDC](https://docs.github.com/en/actions/reference/security/oidc)).
- **Azure DevOps WIF issuer `https://vstoken.dev.azure.com` retires 2027-07-01.** New connections use the Entra issuer and a new subject format ([WIF troubleshooting](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/troubleshoot-workload-identity)).
- **New key vaults default to Azure RBAC** (API 2026-02-01; `az keyvault create` too) ([RBAC guide](https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide)).
- **New subnets are private** (`defaultOutboundAccess=false`) with network API versions after 2026-03-31; VMs need NAT Gateway, firewall via UDR, or a public IP ([default outbound](https://learn.microsoft.com/en-us/azure/virtual-network/ip-services/default-outbound-access)).
- **Mandatory MFA phase 2** (from 2025-10-01) covers CLI, PowerShell, IaC tools, and REST for create/update/delete. Workload identities are exempt; automation signing in as a user breaks ([mandatory MFA](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-mandatory-multifactor-authentication)).
- **Sentinel leaves the Azure portal after 2027-03-31**; Defender portal only ([Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/overview)). MCSB v2 is in preview; ALZ-Bicep Classic is deprecated in favor of AVM.

## Hierarchy and landing zones

| Level | Rules |
|---|---|
| Tenant (Entra) | Identity boundary. Entra roles are separate from Azure RBAC. |
| Tenant root group | ID = tenant ID. Nobody has default access. New subscriptions land here by default. Never put org policy here. |
| Management groups | Max 6 levels deep (excluding root and subscription). One parent each. |
| Subscription | Billing/quota/isolation unit. Max 5,000 role assignments (sub, RG, resource scopes). |
| Resource group | Narrowest recommended scope for workload RBAC. |

CAF layout ([MG design](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone/design-area/resource-org-management-groups)):

```
Tenant root group
└── <prefix>  (intermediate root: org-wide policy goes here)
    ├── Platform: Security, Management, Connectivity, Identity
    ├── Landing zones: Corp (hub-connected), Online (internet-facing)
    ├── Sandbox
    └── Decommissioned
```

- Group MGs by workload type, not org chart (newer CAF says Internal/Online/Local; keep the org's names). Grant workload teams RBAC at subscription or RG, **never at MG scope**. Platform-team MG access goes through PIM.
- Deploy with the ALZ IaC Accelerator (Bicep or Terraform on AVM; phases: plan, prerequisites, bootstrap, run CI/CD) ([implementation options](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone/implementation-options)).
- **GA elevation gotcha**: "Access management for Azure resources" gives a Global Administrator User Access Administrator on every subscription. Alert on it; switch it off after break-glass use ([RBAC vs Entra roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/rbac-and-directory-admin-roles)).

## Entra ID identities

| Type | Credential | Use when |
|---|---|---|
| System-assigned MI | Platform-managed; dies with resource | Per-resource attribution or lifecycle coupling |
| User-assigned MI (UAMI) | Platform-managed; can hold federated credentials; delete manually | CI/CD, AKS, identity shared by several resources |
| App registration + SP | Secret, cert, or federated credential | Multi-tenant apps, Graph permissions, things MI can't do |
| User as service account | Password + MFA | **Never**: mandatory MFA breaks it |

- Conditional Access needs Entra ID P1; roll new policies out in **report-only** first. CA for workload identities needs Workload Identities Premium, covers **single-tenant SPs only**, not managed identities; group membership does not apply CA to an SP ([CA for workload identities](https://learn.microsoft.com/en-us/entra/identity/conditional-access/workload-identity)).
- PIM (Entra ID Governance/P2-class) gives eligible assignments activated just in time with approval, MFA, justification, time limit. Use it for every Owner, User Access Administrator, and RBAC Administrator ([PIM](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure)).
- Keep at least two break-glass accounts with passkeys (FIDO2), excluded from blocking CA, sign-ins monitored ([emergency access](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/security-emergency-access)).
- Mandatory MFA phase 1 (Oct 2024): portal and admin centers; phase 2: CLI/PowerShell/IaC/REST writes; reads exempt. Entra sign-in/audit logs: 7 days Free, 30 days P1/P2; export via diagnostic setting.

### Workload identity federation rules

From [create trust](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust) and [considerations](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-considerations):

- Max 20 federated identity credentials (FICs) per app or UAMI; `issuer`+`subject` unique; one audience, `api://AzureADTokenExchange`.
- **No wildcards; exact match.** A wrong subject is accepted at creation and fails only at token exchange. `name` is immutable.
- New FICs take several minutes to propagate. Retry; don't "fix".
- Flexible FICs (preview) allow `claimsMatchingExpression` with `matches`/`eq`/`and` for GitHub, GitLab, Terraform Cloud. GitHub expressions must match `sub` plus `repository_id` and/or `repository_owner_id`. Azure CLI, PowerShell, and Terraform providers can't create them and error on reading them; use `az rest` against Graph beta or ARM `2025-01-31-preview` ([flexible FIC](https://learn.microsoft.com/en-us/entra/workload-id/workload-identities-flexible-federated-identity-credentials)).

## Authorization: RBAC vs Entra roles

| | Azure RBAC | Entra roles |
|---|---|---|
| Controls | Azure resources (control plane + data actions) | Users, groups, apps, licenses |
| Scopes | MG → subscription → RG → resource | Tenant or administrative unit |
| Key roles | Owner, Contributor, Reader, User Access Administrator, RBAC Administrator | Global Admin, User Admin, Application Admin |

Rules ([RBAC best practices](https://learn.microsoft.com/en-us/azure/role-based-access-control/best-practices)):
- At most **3 subscription Owners**. Assign to groups, at the narrowest scope, job-function roles over admin roles.
- Reference roles by **definition GUID** in automation; names change.
- Any role that can write role assignments gets a **condition** restricting which roles and principals ([delegate with conditions](https://learn.microsoft.com/en-us/azure/role-based-access-control/delegate-role-assignments-overview)).
- Custom roles: one MG max in `AssignableScopes`, no wildcards there; roles with `DataActions` can't be assigned at MG scope.
- You can't create deny assignments directly. Use Deployment Stacks deny settings (`DenyDelete`, `DenyWriteAndDelete`) or the `denyAction` policy effect (DELETE only) ([deployment stacks](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deployment-stacks)).

## Azure Policy

Request-time order: `disabled` → `append`/`modify` → `deny` → `audit` → `manual` → `auditIfNotExists` → `denyAction`; then `auditIfNotExists`/`deployIfNotExists` run after the provider succeeds. Multiple assignments are cumulative most-restrictive ([effect basics](https://learn.microsoft.com/en-us/azure/governance/policy/concepts/effect-basics)).

| Effect | Use | Gotcha |
|---|---|---|
| `deny` | Locations, no public IP, TLS minimum | Breaks deployments; start with `enforcementMode: DoNotEnforce` |
| `audit` / `auditIfNotExists` | Visibility | No remediation |
| `modify` | Tags, toggle properties | Needs an MI with roles; existing resources need remediation |
| `deployIfNotExists` | Diagnostic settings, DNS zone groups | MI with `roleDefinitionIds` roles; existing resources stay non-compliant until a **remediation task** runs ([remediation](https://learn.microsoft.com/en-us/azure/governance/policy/how-to/remediate-resources)) |
| `denyAction` | Block deletes | DELETE only |

## Defender for Cloud

- Foundational CSPM (free): MCSB recommendations, secure score, inventory. Defender CSPM (paid): attack paths, security explorer, agentless VM vuln/secrets scanning, DevOps PR annotations and code-to-cloud mapping ([CSPM](https://learn.microsoft.com/en-us/azure/defender-for-cloud/concept-cloud-security-posture-management)).
- Workload plans: Servers P1/P2, Containers, Storage, Key Vault, Resource Manager, APIs, databases, AI. Classic and Defender-portal secure scores aren't comparable.
- `az security pricing create -n VirtualMachines --tier standard --subplan P2`; other plan names `[unverified]`, run `az security pricing list` first.
- DevOps security connectors: Azure DevOps, GitHub, GitLab. MSDO (`MicrosoftSecurityDevOps@1`, `microsoft/security-devops-action`) bundles Checkov, Template Analyzer/PSRule, Terrascan, Trivy and others; `categories: 'IaC'` for IaC only. Its CredScan is deprecated; use GitHub Advanced Security for secrets.

## Key Vault and Storage

| Setting | Fact |
|---|---|
| Permission model | RBAC default. Access policies let anyone with `vaults/write` (Contributor) grant themselves data access ([RBAC vs access policies](https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-access-policy)) |
| Roles | Key Vault Contributor = control plane only, no secrets. Apps get **Key Vault Secrets User** |
| Soft delete | Always on; retention 7–90 days (default 90), **set at creation only**; deleted vault name blocked until retention ends ([soft delete](https://learn.microsoft.com/en-us/azure/key-vault/general/soft-delete-overview)) |
| Purge protection | **Off by default**; irreversible once on; required by most CMK integrations |

```bash
az keyvault create -g rg-app -n kv-app-prod-001 -l westeurope \
  --enable-rbac-authorization true --enable-purge-protection true \
  --retention-days 90 --public-network-access Disabled
az role assignment create --assignee-object-id <uami-principal-id> \
  --assignee-principal-type ServicePrincipal \
  --role 4633458b-17de-408a-b874-0445c86b69e6 \
  --scope $(az keyvault show -n kv-app-prod-001 --query id -o tsv)
```

`4633458b-...` is Key Vault Secrets User. Passing object ID plus principal type skips a Graph lookup that can race replication `[inference]`.

Storage: Shared Key is **allowed while the property is null** (default); set `--allow-shared-key-access false` after confirming no key users. Keep `--allow-blob-public-access false`, min TLS 1.2 (1.3 minimum not enforceable), `--allow-cross-tenant-replication false`, `--public-network-access Disabled` or `SecuredByPerimeter` ([prevent Shared Key](https://learn.microsoft.com/en-us/azure/storage/common/shared-key-authorization-prevent)).

## Networking

- NSG defaults include `AllowInternetOutBound` (65001) and `AllowVNetInBound`; the `VirtualNetwork` tag spans peered VNets and on-prem, so add explicit east-west denies `[inference]` ([NSG](https://learn.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview)). Existing VMs keep default outbound IPs until the subnet is private **and** the VMs are deallocated.
- Prefer **Private Endpoints** over Service Endpoints: PE is per resource instance, works from on-prem, and is Microsoft's recommendation; Service Endpoints hit the public endpoint and don't work from on-prem ([PE overview](https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-overview)).

Private DNS gotchas ([PE DNS](https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns)):
1. Link the `privatelink.*` zone to the VNet the client uses for DNS; one zone per service type.
2. Hub-spoke: zones centrally in Connectivity; DINE policy creates `privateDnsZoneGroups` ([CAF DNS at scale](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/private-link-and-dns-integration-at-scale)).
3. Changing a VNet's custom DNS servers requires rebooting its VMs.
4. NXDOMAIN trap: a linked zone breaks lookups of other tenants' PE'd accounts. Set fallback to internet (`ResolutionPolicy` NxDomainRedirect) on the link ([fallback](https://learn.microsoft.com/en-us/azure/dns/private-dns-fallback)).
5. On-prem forwards the **public** zone (`blob.core.windows.net`) to a DNS Private Resolver inbound endpoint.
6. NSG/UDR on PE subnets are ignored unless network policies are enabled.
7. Azure Files mounted via the public endpoint must be remounted after adding a PE.

## Logging

- Activity log: kept 90 days; add a **subscription diagnostic setting** to central Log Analytics ([activity log](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log)).
- Resource logs (Key Vault AuditEvent, Storage, Firewall) are **not collected by default**; deploy diagnostic settings via DINE. Max 5 settings per resource ([diagnostic settings](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings)). Plan Sentinel in the Defender portal.

```bash
LAW=$(az monitor log-analytics workspace show -g rg-mgmt -n law-central --query id -o tsv)
az monitor diagnostic-settings subscription create --name activity-to-law --workspace "$LAW" \
  --logs '[{"category":"Administrative","enabled":true},{"category":"Security","enabled":true},{"category":"Policy","enabled":true}]'
```

Category list `[unverified]`; check with `az monitor diagnostic-settings subscription list`.

## CI/CD federation

GitHub `sub` formats ([GitHub OIDC](https://docs.github.com/en/actions/reference/security/oidc)):

| Trigger | `sub` |
|---|---|
| Job with `environment:` | `repo:ORG/REPO:environment:ENV` |
| Branch / tag | `repo:ORG/REPO:ref:refs/heads/BRANCH` / `...:ref:refs/tags/TAG` |
| Pull request, no environment | `repo:ORG/REPO:pull_request` |
| Immutable (new/renamed/transferred after 2026-07-15, or opted in) | `repo:ORG@OWNER_ID/REPO@REPO_ID:...` |

- An `environment:` overrides the ref form, so branch FICs won't match.
- Entra docs write `pull-request`; GitHub issues **`pull_request`**. Trust GitHub.
- Customized `sub` (`include_claim_keys`) must match exactly. Workflow needs `permissions: id-token: write`.

```bash
az identity federated-credential create -g rg-cicd --identity-name id-gh-deploy \
  --name gh-octo-repo-production \
  --issuer https://token.actions.githubusercontent.com \
  --subject "repo:octo-org/octo-repo:environment:Production" \
  --audiences api://AzureADTokenExchange
```

```yaml
permissions: { id-token: write, contents: read }
jobs:
  deploy:
    environment: Production   # sub => repo:ORG/REPO:environment:Production
    steps:
      - uses: azure/login@v3
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
```

- Protect the environment: required reviewers with prevent self-review, branch restrictions. On Free/Pro/Team plans these work only on public repos ([environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
- Terraform azurerm: `ARM_USE_OIDC=true` + client/tenant/subscription IDs. In Azure Pipelines also set `ARM_ADO_PIPELINE_SERVICE_CONNECTION_ID` and `SYSTEM_ACCESSTOKEN`, or it falls back to the GitHub flow ([azurerm OIDC](https://github.com/hashicorp/terraform-provider-azurerm/blob/main/website/docs/guides/service_principal_oidc.html.markdown)).

Azure Pipelines service connections: use app registration or managed identity **with WIF**; convert secret-based ones ([connect to Azure](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/connect-to-azure)).

| | Old issuer (retires 2027-07-01) | New Entra issuer |
|---|---|---|
| Issuer | `https://vstoken.dev.azure.com/<org id>` | `https://login.microsoftonline.com/<tenant id>/v2.0` |
| Subject | `sc://<org>/<project>/<connection name>` | `<entra prefix>/sc/<org id>/<connection id>` |

- Copy issuer and subject from the service connection UI for manual setup. Put Branch control + Required template checks on the **prod service connection** itself `[inference]`; limit job auth scope to the current project ([approvals](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals)).

### What-if limits

`az deployment group what-if -g rg -f main.bicep` or `create ... --confirm-with-what-if`. It expands max 500 nested templates and 800 RGs within 5 minutes (rest shows `Ignore`), short-circuits modules with runtime-dependent IDs or API versions, and shows noise (defaults as deletes). Treat it as a review aid; gate on PSRule/Checkov plus policy `deny` `[inference]` ([what-if](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-what-if)).

## AKS basics

- Managed Entra: `--enable-aad --aad-admin-group-object-ids <grp> --disable-local-accounts`; can't be turned off ([Entra integration](https://learn.microsoft.com/en-us/azure/aks/enable-authentication-microsoft-entra-id)). Add `--enable-azure-rbac`.
- Workload identity: `--enable-oidc-issuer --enable-workload-identity`, UAMI + FIC with subject `system:serviceaccount:<ns>:<sa>` and the cluster issuer URL. Annotate the SA `azure.workload.identity/client-id`, label pods `azure.workload.identity/use: "true"`, read `AZURE_FEDERATED_TOKEN_FILE` ([WI overview](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)).
- Guardrails: `az aks enable-addons --addons azure-policy` (Gatekeeper admission) and the Defender for Containers sensor for runtime detection. Pod-managed identity is deprecated; migrate.

## Debug

| Symptom | Cause | Fix |
|---|---|---|
| `AADSTS70021` no matching federated identity record | `sub`/`iss` mismatch: rename, immutable format, environment vs ref, `vstoken` vs Entra issuer | Dump real token claims or copy issuer/subject from the ADO connection; compare character by character |
| Login fails right after FIC creation | Propagation delay | Wait minutes, retry |
| `RoleAssignmentLimitExceeded` | 5,000 per subscription | Consolidate onto groups |
| `RequestDisallowedByPolicy` | `deny` assignment | `az policy assignment show` on the listed ID; request an exemption |
| DINE resources stay non-compliant | No remediation task or MI lacks role | Create remediation task; check `roleDefinitionIds` |
| App resolves public IP of PE'd service | Zone not linked or wrong forwarder | `nslookup` from client network |
| NXDOMAIN for partner storage | Linked zone lacks record | Fallback to internet (`ResolutionPolicy`) |
| Owner gets 403 on secrets | RBAC vault; Owner is control plane | Assign Key Vault Secrets User/Officer |
| Can't reuse vault name | Soft-deleted vault holds it | `az keyvault list-deleted`; recover, or purge if protection off |
| VM has no internet on new VNet | Private subnet default | NAT Gateway or firewall UDR |
| AKS pod gets no token | Missing pod label, SA annotation, or wrong FIC subject | Fix label/annotation/`system:serviceaccount:ns:sa` |
| CLI automation suddenly needs MFA | User account hits mandatory MFA phase 2 | Move to a workload identity |

## Hardening checklist

**P0: day 0**
1. Place the subscription under the right landing-zone MG (never tenant root).
2. ≤3 Owners, all PIM-eligible; no standing Owner/UAA; remove creator's direct Owner.
3. Two passkey break-glass accounts, CA baseline (MFA all users, block legacy auth), no automation as users.
4. Deployment UAMI with FICs for `environment:Prod` (deploy) and `pull_request` (plan); Contributor on target RGs only, Reader for plan; no secrets.
5. Subscription diagnostic setting: activity log to central Log Analytics.

**P1: week 1**
6. Verify inherited ALZ policies (locations, no public IP on NICs, storage public access, KV purge protection, DINE diagnostics and DNS zone groups) with `az policy state summarize`.
7. Defender CSPM plus the workload plans in use; review secure score and attack paths.
8. Connect the repo org to Defender DevOps security; add MSDO or PSRule + Checkov to PRs.
9. Network: hub peering, private subnets, firewall egress via UDR, NSGs with east-west denies, PEs for PaaS with central DNS.
10. Key Vault: RBAC, purge protection, PE, `AuditEvent` diagnostics; apps use Secrets User via MI.
11. Storage: Shared Key off, anonymous off, TLS 1.2, PE or perimeter, cross-tenant replication off.

**P2: month 1**
12. Resource-log diagnostics via policy; Entra logs and Defender alerts to Sentinel.
13. AKS: managed Entra, local accounts off, Azure RBAC, workload identity, policy add-on, Defender sensor.
14. Prod RGs as deployment stacks with `DenyDelete`, or `denyAction` policy.
15. ADO: Branch control + Required template on prod connection, project-scoped job auth. GitHub: reviewers with self-review blocked, `sub` customized with `repository_id`.
16. Quarterly access reviews of privileged roles and workload identities (CA doesn't cover MIs).

## Do / Avoid

**Do**
- UAMI + FICs for CI/CD and AKS; environment-scoped GitHub FICs; separate Reader identity for PR/plan.
- Roles by GUID, to groups, narrowest scope; PIM for privileged roles; conditions on role-assigning roles.
- Org policy on an intermediate root MG; `deny` as `DoNotEnforce` first; remediation tasks for DINE/Modify.
- New vaults: RBAC, purge protection, public access off, PE; choose retention deliberately.
- Central `privatelink.*` zones with DINE zone groups and internet fallback where needed.
- Pin `azure/login@v3`, `microsoft/ps-rule@v2.9.0`, Checkov; third-party actions by SHA `[inference]`.

**Avoid**
- Client secrets, `--sdk-auth` JSON, publish profiles, user accounts as service accounts.
- Wildcards in classic FICs; flexible GitHub FICs without an immutable ID claim.
- Key Vault access policies; standing Owner/UAA; MG-scope RBAC for workload teams.
- What-if as the only gate; Service Endpoints as the isolation story; assuming PE-subnet NSGs apply.
- Leaving GA elevation on; new work on ALZ-Bicep Classic or pod-managed identity; new manual FICs on `vstoken.dev.azure.com`.

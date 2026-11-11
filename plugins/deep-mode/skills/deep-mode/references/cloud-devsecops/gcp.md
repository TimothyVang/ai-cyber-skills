# Google Cloud security and DevSecOps

Read when designing, reviewing, debugging, or hardening a Google Cloud org, project, IAM policy, org policy, VPC Service Controls perimeter, network, KMS/Secret Manager setup, logging/SCC, supply-chain pipeline, GitHub-to-GCP federation, or GKE cluster. Facts as of 2026-11-11; `[inference]` and `[unverified]` marks are kept from the report.

Full report: https://github.com/TimothyVang/cloud-devsecops/blob/main/research/gcp-devsecops.md

## Know first

- Orgs created on or after 2024-05-03 get a [security baseline](https://docs.cloud.google.com/resource-manager/docs/secure-by-default-organizations): SA key creation/upload off, no auto-Editor on default SAs, domain-restricted sharing, in-domain Essential Contacts, internal-only protocol forwarding, uniform bucket-level access. Older orgs usually lack it; check with `gcloud resource-manager org-policies list --organization=ORG_ID`.
- Many constraints have a `*.managed.*` form beside the legacy one (e.g. `iam.managed.disableServiceAccountKeyCreation` vs `iam.disableServiceAccountKeyCreation`). In Terraform review, look for both `[inference]`.
- SA keys are the top credential risk; Google says avoid them [whenever possible](https://docs.cloud.google.com/iam/docs/best-practices-service-accounts).
- Data Access audit logs are OFF by default except BigQuery ([audit logs](https://docs.cloud.google.com/logging/docs/audit)).
- SCC Enterprise is deprecated (shutdown 2027-05-21); threat detection needs **Premium** ([tiers](https://docs.cloud.google.com/security-command-center/docs/service-tiers)).
- New basic roles `roles/admin|writer|reader` exist next to `roles/owner|editor|viewer`; both are too broad for prod ([roles](https://docs.cloud.google.com/iam/docs/roles-overview)).
- Google ships agent skills: `npx skills add google/skills --skill google-cloud-waf-security` ([google/skills](https://github.com/google/skills)).

## Hierarchy and foundations

- Org → folders (up to 10 deep, 300 direct children) → projects → resources. Allow and org policies inherit downward ([hierarchy](https://docs.cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy), [limits](https://docs.cloud.google.com/resource-manager/docs/limits)).
- Folders by environment and business unit; attach org policies, hierarchical firewall policies, and deny policies at folders `[inference]`.
- One workload per environment per project; the project is the isolation, quota and IAM boundary `[inference]`.
- Shared security services (logging, SCC, KMS, secrets, WIF pool, CI seed) live in dedicated projects under `common` `[inference]`.

The [enterprise foundations blueprint](https://docs.cloud.google.com/architecture/blueprints/security-foundations) (Terraform: [terraform-example-foundation](https://github.com/terraform-google-modules/terraform-example-foundation)) does GitOps via Cloud Build with policy checks, roles to groups by job function, humans view-only on foundations, Shared VPC per env with no internet path by default, and central logging/KMS/secrets.

Stages: `0-bootstrap` (seed state bucket + per-stage SAs, CI/CD project; run once by hand), `1-org` (common logging/SCC/KMS/secrets projects, network folder, org sinks), `2-environments` (per-env kms and secrets), `3-networks-*` (Shared VPC, hierarchical firewall, `restricted.googleapis.com`), `4-projects`, `5-app-infra`.

Gotcha: the blueprint keeps audit logs in BigQuery for only 30 days by default; raise it or add a locked bucket if compliance needs more.

## IAM

### Roles and service accounts
- Never grant basic roles (legacy or new) in prod. Legacy basic roles can't take IAM Conditions. Pick the narrowest predefined role; custom roles only when predefined are too broad.
- Default Compute/App Engine SAs used to get `roles/editor` automatically; `iam.automaticIamGrantsForDefaultServiceAccounts` stops it. Never run workloads as default SAs.
- SA key threats: leakage (repos, buckets, backups, temp dirs), privilege escalation, disclosure, non-repudiation ([keys](https://docs.cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys)). Keys never expire by default; cap with `iam.serviceAccountKeyExpiryHours` (one of `1h..2160h`, must replace parent policy).
- `iam.serviceAccountKeyExposureResponse` defaults to `DISABLE_KEY`: Google disables publicly leaked keys. Keep it.
- Prefix SA names by use (`vm-`, `wlifgke-`, `wlif-`); disable unused SAs before deleting.
- Cloud Build's default SA varies by org history; always set a user-specified SA ([Cloud Build SA](https://docs.cloud.google.com/build/docs/cloud-build-service-account)).

### Impersonation (instead of keys)
Caller needs `roles/iam.serviceAccountTokenCreator` on the target SA ([impersonation](https://docs.cloud.google.com/docs/authentication/use-service-account-impersonation)). Grant it (and `serviceAccountUser`) on the SA, never at project level, which covers every SA `[inference]`.

```bash
gcloud storage buckets list --impersonate-service-account=deployer@prj.iam.gserviceaccount.com
gcloud config set auth/impersonate_service_account deployer@prj.iam.gserviceaccount.com
gcloud auth application-default login --impersonate-service-account deployer@prj.iam.gserviceaccount.com
```

### Conditions, deny, PAB
- [Conditions](https://docs.cloud.google.com/iam/docs/conditions-overview) are CEL on bindings: `request.time < timestamp("2026-12-01T00:00:00Z")` for break-glass, `resource.matchTag('123456789012/env', 'prod')` for tag scope. Not allowed with legacy basic roles or `allUsers`/`allAuthenticatedUsers`.
- [Deny policies](https://docs.cloud.google.com/iam/docs/deny-overview) are checked before allow; up to 500 rules per resource; permissions use `SERVICE.googleapis.com/resource.verb`.

```json
{ "rules": [ { "denyRule": {
  "deniedPrincipals": ["principalSet://goog/public:all"],
  "exceptionPrincipals": ["principalSet://goog/group/platform-admins@example.com"],
  "deniedPermissions": ["cloudresourcemanager.googleapis.com/projects.delete"]
}}]}
```

- [Principal Access Boundary](https://docs.cloud.google.com/iam/docs/principal-access-boundary-policies) limits which resources a principal may use regardless of allow grants (e.g. block other orgs). Bound to principal sets; binding conditions use only `principal.type`/`principal.subject`. Don't pin enforcement version `latest`: a new default can remove access. Cross-org bindings get deleted after project moves.
- Layers `[inference]`: allow (on resource: who may do what here), deny (on resource: what nobody may do here), PAB (on principal set: where this principal may act at all).
- Role recommender uses up to 90 days of usage ([recommender](https://docs.cloud.google.com/policy-intelligence/docs/role-recommendations-overview)); Policy Simulator previews allow changes. PAM gives just-in-time, approved, time-limited grants ([PAM](https://docs.cloud.google.com/iam/docs/pam-overview)); licensing `[unverified]`.

## Org policy constraints

Use `dryRunSpec` first: `gcloud org-policies set-policy FILE --update-mask=dryRunSpec` ([dry-run](https://docs.cloud.google.com/resource-manager/docs/organization-policy/dry-run-policy)). A tag-conditional rule needs an unconditional rule too. Custom constraints are CEL over resource fields.

```yaml
name: organizations/ORG_ID/policies/iam.managed.disableServiceAccountKeyCreation
spec:
  rules:
  - enforce: true
```

| Goal | Constraint ([list](https://docs.cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints)) |
|---|---|
| No SA keys / uploads (baseline) | `iam.managed.disableServiceAccountKeyCreation`, `iam.managed.disableServiceAccountKeyUpload` |
| No Editor on default SAs (baseline) | `iam.automaticIamGrantsForDefaultServiceAccounts` |
| Domain-restricted sharing (baseline) | `iam.managed.allowedPolicyMembers` (legacy `iam.allowedPolicyMemberDomains`) |
| Contacts / forwarding (baseline) | `essentialcontacts.managed.allowedContactDomains`, `compute.managed.restrictProtocolForwardingCreationForTypes` |
| Buckets | `storage.uniformBucketLevelAccess` (baseline), `storage.publicAccessPrevention`, `storage.secureHttpTransport` |
| VMs | `compute.managed.vmExternalIpAccess`, `compute.managed.requireOsLogin`, `compute.requireShieldedVm`, `compute.managed.disableSerialPortAccess`, `compute.managed.vmCanIpForward` |
| Network | `compute.skipDefaultNetworkCreation`, `compute.restrictVpcPeering` |
| Cloud SQL | `sql.restrictPublicIp`, `sql.restrictAuthorizedNetworks` |
| Location / CMEK | `gcp.resourceLocations`, `gcp.restrictNonCmekServices`, `gcp.restrictCmekCryptoKeyProjects` |
| Serverless | `run.allowedIngress`, `cloudfunctions.allowedIngressSettings`, `run.managed.requireInvokerIam` (blocks public unauthenticated Run) |
| WIF / SA misc | `iam.managed.workloadIdentityPoolProviders`, `iam.disableCrossProjectServiceAccountUsage`, `iam.managed.disableServiceAccountApiKeyCreation`, `compute.managed.blockPreviewFeatures` |
| GKE | `container.managed.*`: `enableWorkloadIdentityFederation`, `enablePrivateNodes`, `enableShieldedNodes`, `enableNetworkPolicy`, `enableBinaryAuthorization`, `enableSecretsEncryption`, `enableControlPlaneDNSOnlyAccess`, `disallowDefaultComputeServiceAccount`, `disableInsecureKubeletReadOnlyPort`, `denyServiceExternalIPs`, and more |

Rollout `[inference]`: dry-run at org → watch violations 1–2 weeks → enforce → tag-conditioned exceptions for named projects only.

## VPC Service Controls

- A perimeter around projects and Google APIs (GCS, BigQuery, Secret Manager) that blocks data crossing it, independent of IAM; run both ([overview](https://docs.cloud.google.com/vpc-service-controls/docs/overview)).
- Pieces: access levels, ingress/egress rules, VPC-accessible services, `restricted.googleapis.com` (`199.36.153.4/30`).
- Always [dry-run](https://docs.cloud.google.com/vpc-service-controls/docs/dry-run-mode) first.

```bash
gcloud access-context-manager perimeters create prod_perimeter \
  --title="prod" --policy=POLICY_NUMBER \
  --resources=projects/111111111111,projects/222222222222 \
  --restricted-services=storage.googleapis.com,bigquery.googleapis.com,secretmanager.googleapis.com \
  --ingress-policies=ingress.yaml --egress-policies=egress.yaml \
  --enable-vpc-accessible-services --vpc-allowed-services=RESTRICTED-SERVICES
```

## Networking

- Cloud NGFW tiers: Essentials (free L3/L4, secure tags), Standard (FQDN, threat intel), Enterprise (IDS/IPS, URL filtering) ([NGFW](https://docs.cloud.google.com/firewall/docs/about-firewalls)).
- [Evaluation order](https://docs.cloud.google.com/firewall/docs/firewall-policies-rule-eval-order): hierarchical (org → folders) → regional system → classic VPC rules (default `AFTER_CLASSIC_FIREWALL`) → global network → regional network → implied. `goto_next` hands off. Implied: VM ingress denied, egress allowed, internal ALB/proxy NLB ingress allowed.
- Use IAM-governed secure tags for segmentation, not network tags (anyone with instance edit can set those) `[inference]`.
- Private Google Access is per subnet, only for VMs without external IPs. PSC bundles: `all-apis` or `vpc-sc` ([PSC](https://docs.cloud.google.com/vpc/docs/configure-private-service-connect-apis)).
- IAP TCP needs ingress from `35.235.240.0/20` plus `roles/iap.tunnelResourceAccessor` ([IAP TCP](https://docs.cloud.google.com/iap/docs/using-tcp-forwarding)). Apps behind IAP must verify `x-goog-iap-jwt-assertion` ([signed headers](https://docs.cloud.google.com/iap/docs/signed-headers-howto)).
- Cloud Armor on external LBs: OWASP preconfigured rules, rate limiting; Enterprise adds Adaptive Protection and threat intel ([Armor](https://docs.cloud.google.com/armor/docs/cloud-armor-overview)).

## KMS, Secret Manager, SDP

- CMEK (manual or [Autokey](https://docs.cloud.google.com/kms/docs/autokey-overview)) gives rotation, metadata, org policies, and key-access logs. Autokey defaults: HSM, AES-256-GCM, 1-year rotation, dedicated key project per folder or same-project.
- Protection levels: `SOFTWARE`, `HSM`, `HSM_SINGLE_TENANT`, `EXTERNAL`, `EXTERNAL_VPC` ([levels](https://docs.cloud.google.com/kms/docs/protection-levels)). Destruction is scheduled, 30 days by default, restorable meanwhile.
- Keep KMS admins separate from encrypter/decrypters, and keys in separate projects `[inference]`.
- [Secret Manager](https://docs.cloud.google.com/secret-manager/docs/best-practices): secret-level IAM, separate env projects, ADC not keys, prefer API calls over env vars/files (serverless integrations excepted), pin versions not `latest`, disable ~1 week before destroy, rotate, Data Access logs for `AccessSecretVersion`, VPC SC perimeter, plan quota for mass pod starts.
- [Sensitive Data Protection](https://docs.cloud.google.com/sensitive-data-protection/docs/sensitive-data-protection-overview) discovery profiles BigQuery, Cloud SQL, GCS org-wide; findings feed SCC and raise ETD severity.

## Audit logs and SCC

| Log | Default | Disable? | Bucket |
|---|---|---|---|
| Admin Activity | On | No | `_Required` (400 days, fixed) |
| System Event | On | No | `_Required` |
| Data Access | Off except BigQuery | Yes, per service or `allServices` | `_Default` (30 days) |
| Policy Denied | On, billed | Exclude only | `_Default` |

- Aggregated sink at org with `--include-children`; grant the sink's writer identity on the destination; lock buckets for compliance ([sinks](https://docs.cloud.google.com/logging/docs/export/aggregated_sinks)).
- Admin Activity always lands in the source project's `_Required`; routed copies skip the destination's `_Required`/`_Default` sinks.
- Enable Data Access via `auditConfigs` on the org IAM policy; `exemptedMembers` cuts noise ([configure](https://docs.cloud.google.com/logging/docs/audit/configure-data-access)).

```bash
gcloud logging sinks create org-audit \
  logging.googleapis.com/projects/prj-c-logging/locations/global/buckets/org-audit \
  --organization=ORG_ID --include-children \
  --log-filter='logName:"cloudaudit.googleapis.com"'
```

- SCC Standard: free, no threat detection, no SHA for new activations. Premium: SHA with CIS/NIST/PCI mapping, Event/Container/VM/Cloud Run Threat Detection, attack paths. Enterprise adds multi-cloud and SecOps but is deprecated.
- [ETD](https://docs.cloud.google.com/security-command-center/docs/concepts-event-threat-detection-overview) detectors stay silent if their source is off: enable VPC Flow Logs, Cloud DNS logs, and needed Data Access logs `[inference]`.

## Supply chain

- Cloud Build emits SLSA L3 provenance; set `options: requestedVerifyOption: VERIFIED`. Inspect with `gcloud artifacts docker images describe IMAGE@sha256:HASH --show-provenance`; verify with `slsa-verifier` ≥ 2.1 ([provenance](https://docs.cloud.google.com/build/docs/securing-builds/generate-validate-build-provenance)).
- Artifact Analysis: enable `containerscanning.googleapis.com`; scans on push, continuous only for images pulled in the last 30 days; detects malicious packages ([scanning](https://docs.cloud.google.com/artifact-analysis/docs/container-scanning-overview)).
- CI gate: `gcloud artifacts docker images scan IMAGE --format='value(response.scan)'` then `list-vulnerabilities SCAN_ID`; needs `roles/ondemandscanning.admin` ([ODS](https://docs.cloud.google.com/artifact-analysis/docs/ods-cloudbuild)).
- [Binary Authorization](https://docs.cloud.google.com/binary-authorization/docs/policy-yaml-reference): `evaluationMode` `REQUIRE_ATTESTATION` with attestors; `enforcementMode` `DRYRUN_AUDIT_LOG_ONLY` then `ENFORCED_BLOCK_AND_AUDIT_LOG`. Alert on `break-glass` label use. Continuous validation is Preview.
- Assured OSS: SLSA L3 packages; free tier Python/Go/Java, npm needs Premium.

Pipeline order `[inference]`: GitHub Actions via WIF → Cloud Build as dedicated SA with provenance `VERIFIED` → Artifact Registry with scanning plus ODS gate → deploy by digest → Binary Authorization dry-run, then enforce → continuous validation and SCC for drift.

## GitHub Actions → GCP (Workload Identity Federation)

Rules ([WIF best practices](https://docs.cloud.google.com/iam/docs/best-practices-for-using-workload-identity-federation), [pipelines](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines), [auth security](https://github.com/google-github-actions/auth/blob/main/docs/SECURITY_CONSIDERATIONS.md)):
- Always set an attribute condition: GitHub shares one issuer, so without it any repo in the world can authenticate.
- A condition can only test claims that are in the attribute mapping. Map first.
- Use numeric `repository_owner_id` / `repository_id`; names can be re-registered.
- Dedicated WIF project; `iam.workloadIdentityPoolProviders` deny-all at root except that project; one provider per pool.
- Never `*` in principalSet bindings. Members use the project **number**, not ID. `gcp-` prefix is reserved.
- Direct WIF (roles on `principalSet://…`) is preferred; some APIs reject federated tokens, so fall back to SA impersonation via `roles/iam.workloadIdentityUser`. Never `credentials_json`.

```bash
gcloud iam workload-identity-pools providers create-oidc my-org \
  --project=$PROJECT --location=global --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository_id=assertion.repository_id,attribute.repository_owner_id=assertion.repository_owner_id,attribute.ref=assertion.ref,attribute.environment=assertion.environment" \
  --attribute-condition="assertion.repository_owner_id == '${ORG_ID_GH}' && assertion.repository_id == '${REPO_ID_GH}' && (assertion.ref == 'refs/heads/main' || assertion.environment == 'production')"
POOL="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github"
gcloud artifacts repositories add-iam-policy-binding app-images \
  --project=prj-p-app --location=europe-west1 --role=roles/artifactregistry.writer \
  --member="principalSet://iam.googleapis.com/${POOL}/attribute.repository_id/${REPO_ID_GH}"
```

```yaml
permissions:
  contents: read
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4            # pin to full SHA
      - uses: google-github-actions/auth@v3  # pin to full SHA
        with:
          project_id: prj-p-app
          workload_identity_provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/my-org
```

Tighten `[inference]`: pin `assertion.job_workflow_ref` to a trusted reusable workflow; separate prod/nonprod providers; GitHub environments with required reviewers. GitLab: `assertion.namespace_id=='GROUP_ID'`.

## GKE

- [WIF for GKE](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/workload-identity): pool `PROJECT_ID.svc.id.goog`, metadata server on each node. Bind to `principal://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/PROJECT_ID.svc.id.goog/subject/ns/NAMESPACE/sa/KSA`.
- Same namespace/KSA in two clusters of one project is the same IAM identity; isolate sensitive clusters in separate projects.
- Autopilot defaults: WIF on, Shielded nodes, COS, release channel, no privileged pods or host namespaces, drops `CAP_NET_RAW`, no node SSH ([Autopilot](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-security)).
- Standard [hardening](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster): no default compute SA for nodes, COS, DNS-only control-plane endpoint, private nodes, NetworkPolicy, Google Groups RBAC, auto-upgrade, kubelet port 10255 off, KMS Secrets encryption, GKE Sandbox, Policy Controller.
- Posture dashboard vulnerability scanning is shut down (OS 2025-07-31, Advanced 2026-06-16); use Artifact Analysis/SCC.

## Debug

| Symptom | Cause | Fix |
|---|---|---|
| CI fails with `VPC_SERVICE_CONTROLS` | Runner identity outside perimeter | Add an ingress rule for the pipeline identity; read Policy Denied logs `[inference]` |
| IAM allow looks right, still denied | Deny policy or PAB | Check deny policies, PAB, Policy Troubleshooter |
| GitHub auth: token can't be minted | Missing `id-token: write` (declaring `permissions` drops defaults) | Add it at workflow or job level |
| WIF auth rejected right after setup | Pool/provider/IAM propagation up to 5 min | Wait, retry |
| WIF condition never matches | Claim not in attribute mapping | Map the claim first |
| `principalSet` binding has no effect | Project ID used instead of number | Use the project number |
| API rejects federated token | Not all APIs accept direct WIF | Use WIF + SA impersonation |
| `gsutil` ignores CI credentials | `gsutil` doesn't read exported creds | Use `gcloud storage` |
| ETD finds nothing | Source logs off | Enable Flow Logs, DNS logs, Data Access logs |
| Audit history missing after 30 days | `_Default` retention | Org sink to a longer, locked bucket |
| Unsigned `x-goog-authenticated-user-*` trusted | IAP bypass possible | Verify the IAP JWT |
| Image scan data missing | Not pulled in 30 days / scanning off | Enable scanning; ODS in CI |

## Hardening checklist

P0 (days 0–7):
1. Few dedicated super admins with security keys; Org Admin to a group ([super admin](https://docs.cloud.google.com/resource-manager/docs/super-admin-best-practices)).
2. Confirm baseline org policies; add missing ones on older orgs.
3. Dry-run then enforce: `storage.publicAccessPrevention`, `compute.managed.vmExternalIpAccess`, `sql.restrictPublicIp`, `compute.skipDefaultNetworkCreation`, `compute.managed.requireOsLogin`, `compute.requireShieldedVm`, `iam.managed.workloadIdentityPoolProviders`, `gcp.resourceLocations`, `run.managed.requireInvokerIam`.
4. Roles to groups; find basic roles: `gcloud asset search-all-iam-policies --scope=organizations/ORG_ID --query='policy:(roles/owner OR roles/editor OR roles/admin OR roles/writer)'` `[inference]`.
5. No SA keys: CI to WIF, humans to impersonation, delete user-managed keys (`gcloud iam service-accounts keys list --iam-account=SA --managed-by=user`).
6. Remove Editor from default SAs in older projects.
7. Org aggregated audit sink to `prj-c-logging`, locked ≥ 365 days.
8. SCC Standard minimum, Premium for prod orgs; findings to Pub/Sub → on-call.
9. Essential Contacts, in-domain only.

P1 (first month): foundation folders via IaC pipeline; hierarchical firewall (IAP + health checks, deny 22/3389 from `0.0.0.0/0`), Shared VPC, PGA/PSC, Cloud NAT; Data Access logs for IAM, Secret Manager, KMS, sensitive GCS/BigQuery; Secret Manager per env; Autokey + CMEK constraints; supply-chain pipeline above; GKE Autopilot with `container.managed.*`; monthly recommender review.

P2 (first quarter): VPC SC (2+ weeks dry-run); deny policies on prod folders; PAB against other orgs; PAM instead of standing admin; Cloud Armor on external LBs; IAP with JWT checks; SDP discovery; Policy Controller and continuous validation; custom constraints.

## Do / Avoid

Do:
- Read effective org policies before proposing infra (`gcloud org-policies describe CONSTRAINT --effective` `[inference]`).
- Narrowest predefined role at the lowest resource; Conditions for time and tag scope.
- WIF for CI, WIF for GKE for pods, attached SAs for VMs/Run, impersonation for humans.
- Provider-level attribute condition on numeric IDs **and** narrow principalSet bindings.
- Dry-run every guardrail: `dryRunSpec`, VPC SC dry-run, `DRYRUN_AUDIT_LOG_ONLY`.
- Pin images by digest and secrets by version.

Avoid:
- Basic roles in prod; project-level `serviceAccountUser`/`serviceAccountTokenCreator`.
- SA JSON keys or `credentials_json` in GitHub Actions.
- WIF providers without conditions, `principalSet://…/*`, conditions on mutable names alone.
- Public IPs on VMs/Cloud SQL, the default network, `0.0.0.0/0` to 22/3389.
- `allUsers`/`allAuthenticatedUsers` unless deliberately public and documented.
- Assuming Data Access logs exist, `_Default` keeps over 30 days, or SCC Standard detects threats.

Staleness: SCC tiers, managed-vs-legacy constraint names, PAB enforcement versions, and GitHub OIDC claims change often; re-check the linked docs. Sibling files: `aws.md`, `azure.md`, `devsecops-pipeline.md`.

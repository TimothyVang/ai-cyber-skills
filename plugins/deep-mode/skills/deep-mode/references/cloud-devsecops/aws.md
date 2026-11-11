# AWS security and DevSecOps

Read when designing, reviewing, debugging, or securing AWS accounts, organizations, IAM, detection, encryption, network controls, CI/CD into AWS, or IaC for AWS. Facts and prices are as of 2026-11-11 (us-east-1 list prices; treat as order of magnitude). Pipeline-generic rules live in `devsecops-pipeline.md`.

Full report: https://github.com/TimothyVang/cloud-devsecops/blob/main/research/aws-devsecops.md

## Organization structure

Use the [AWS SRA layout](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/architecture.html):

| OU / account | Holds | Notes |
|---|---|---|
| Management | Organizations, billing, Identity Center, Control Tower | No workloads; SCPs don't apply |
| Security → Security Tooling | Delegated admin for GuardDuty, Security Hub, Inspector, Macie, Detective, Access Analyzer, Config aggregator | Restrict logins |
| Security → Log Archive | Org CloudTrail bucket, Config delivery, flow logs | Object Lock, deny deletes `[inference]` |
| Infrastructure → Network | TGW/Cloud WAN, central egress, Network Firewall, DNS Firewall | |
| Infrastructure → Shared Services | Directory, CI tooling, shared AMIs | |
| Workloads | One account per app per env | Account = blast-radius boundary `[inference]` |

- SRA example code (v3.1.0, Feb 2024) may be stale.
- [Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/how-control-tower-works.html) controls are preventive (SCP/RCP/declarative), detective (Config rules), or proactive (CFN hooks before deploy). They apply per OU; the management account is exempt but logged.
- Landing zone 4.0 no longer requires a Security OU. Never hand-edit Control Tower-created resources: controls can end up in an unknown state.
- Root: centralize [root access](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html#id_root-user-access-management) and delete member-account root passwords, keys and MFA; new members get no root credentials. Root-only tasks run as "privileged tasks".
- Administer security services from Security Tooling, not management. Unified Security Hub is enabled via Organizations policies, not CSPM central configuration ([FAQ](https://aws.amazon.com/security-hub/faqs/)).

## Organization policies

| | SCP | RCP | Declarative |
|---|---|---|---|
| Limits | Principals in member accounts | Resources in member accounts (any caller, incl. external and root) | Service configuration |
| Grants? | Never | Never | n/a |
| Affects service-linked roles | No | No | **Yes** |
| Affects management account | No | No | `[unverified]` |
| Max size / per target | 10,240 chars / 10 | 5,120 chars / 5 (`RCPFullAWSAccess` counts) | 10,000 chars / 10 |

Sources: [limits](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html), [RCPs](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html), [declarative](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_declarative.html).

- RCPs need all features enabled and apply only to services on the supported list (S3, STS, KMS, SQS, Secrets Manager, DynamoDB, ECR, Cognito, CloudWatch Logs, more). Test on a sandbox OU before root `[inference]`.
- Declarative policies enforce config (IMDS defaults, allowed AMIs) and roll back when detached.
- Org-level S3 Block Public Access uses the Organizations **S3 policy** and overrides account settings.
- Region-deny SCPs must exempt global services (IAM, Organizations, Route 53, CloudFront, STS, support, billing) via `NotAction` + `aws:RequestedRegion`. Copy the maintained example from [service-control-policy-examples](https://github.com/aws-samples/service-control-policy-examples) `[inference]`.

Starter SCP (illustrative action list `[inference]`):

```json
{ "Version": "2012-10-17", "Statement": [
  { "Sid": "DenyLeaveOrg", "Effect": "Deny", "Action": "organizations:LeaveOrganization", "Resource": "*" },
  { "Sid": "ProtectSecurityServices", "Effect": "Deny", "Resource": "*",
    "Action": ["cloudtrail:StopLogging","cloudtrail:DeleteTrail","cloudtrail:UpdateTrail","cloudtrail:PutEventSelectors","guardduty:DeleteDetector","guardduty:DisassociateFromAdministratorAccount","guardduty:UpdateDetector","config:StopConfigurationRecorder","config:DeleteConfigurationRecorder","config:DeleteDeliveryChannel","securityhub:DisableSecurityHub","access-analyzer:DeleteAnalyzer","ec2:DisableEbsEncryptionByDefault","s3:PutAccountPublicAccessBlock"],
    "Condition": { "ArnNotLike": { "aws:PrincipalArn": "arn:aws:iam::*:role/SecurityBreakGlass" } } },
  { "Sid": "DenyRootInMembers", "Effect": "Deny", "Action": "*", "Resource": "*", "Condition": { "StringLike": { "aws:PrincipalArn": "arn:aws:iam::*:root" } } } ] }
```

Starter RCP (org identity perimeter + TLS-only, pattern from [data-perimeter-policy-examples](https://github.com/aws-samples/data-perimeter-policy-examples)):

```json
{ "Version": "2012-10-17", "Statement": [
  { "Sid": "EnforceOrgIdentities", "Effect": "Deny", "Principal": "*", "Action": ["s3:*","sqs:*","kms:*","secretsmanager:*","sts:AssumeRole"], "Resource": "*",
    "Condition": { "StringNotEqualsIfExists": { "aws:PrincipalOrgID": "o-exampleorgid" }, "BoolIfExists": { "aws:PrincipalIsAWSService": "false" } } },
  { "Sid": "EnforceTLS", "Effect": "Deny", "Principal": "*", "Action": ["s3:*","sqs:*","kms:*","secretsmanager:*","sts:*"], "Resource": "*",
    "Condition": { "BoolIfExists": { "aws:SecureTransport": "false" } } } ] }
```

Identity perimeters break legit third-party access (vendor SaaS roles, CloudFront OAC). Add exceptions via `aws:PrincipalAccount` allow-lists or `aws:SourceArn`/`aws:SourceAccount` for service principals `[inference]`.

## IAM

- Order of [best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html): federate humans; roles for workloads (off-AWS: IAM Roles Anywhere, ECS Anywhere, EKS Hybrid Nodes, SSM hybrid); MFA; rotate only unavoidable keys; protect root; least privilege; generate policies from activity; remove unused access; use conditions; verify public/cross-account access; validate policies; SCP/RCP guardrails; permissions boundaries to delegate.
- Identity Center sessions default to 1 h, configurable 1–12 h. Small permission sets assigned to SCIM-synced **groups**, never individuals `[inference]`.
- **Permissions boundary** caps what identity policies can grant. Pattern: allow `iam:CreateRole` only when `iam:PermissionsBoundary` equals your boundary ARN; deny altering the boundary `[inference]`.
- **Session policies** narrow an assumed session and never grant; useful to limit a CI job to one stack `[inference]`.
- An explicit Deny anywhere wins; SCPs/RCPs only filter.
- [Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html): external analyzer (re-analysis ~30 min, up to 24 h for RCP changes), internal analyzer, unused-access analyzer (paid), free validation, paid custom checks (`check-no-new-access`, `check-access-not-granted`, `check-no-public-access`), policy generation from CloudTrail.

```bash
aws accessanalyzer validate-policy --policy-type IDENTITY_POLICY --policy-document file://p.json
aws accessanalyzer check-no-public-access --resource-type AWS::S3::Bucket --policy-document file://bucket.json
aws accessanalyzer check-access-not-granted --policy-type IDENTITY_POLICY \
  --policy-document file://p.json --access '[{"actions":["iam:PassRole","s3:DeleteBucket"]}]'
```

For CFN templates, [`cfn-policy-validator`](https://github.com/awslabs/aws-cloudformation-iam-policy-validator) runs these checks on embedded policies.

### Condition keys

| Key | Use |
|---|---|
| `aws:PrincipalOrgID`, `aws:PrincipalOrgPaths` | Identity perimeter |
| `aws:ResourceOrgID` | Resource perimeter (identity policy or SCP) |
| `aws:SourceVpc`, `aws:SourceVpce` | Network perimeter |
| `aws:SourceArn`, `aws:SourceAccount`, `aws:SourceOrgID`, `aws:SourceOrgPaths` | [Confused deputy](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html) protection for service principals |
| `aws:PrincipalIsAWSService`, `aws:ViaAWSService`, `aws:CalledVia` | Exempt AWS-service calls from perimeter denies |
| `aws:SecureTransport` / `aws:RequestedRegion` / `aws:MultiFactorAuthPresent` | TLS-only / region limits / MFA gating |
| `aws:PrincipalTag/*`, `aws:ResourceTag/*`, `aws:RequestTag/*`, `aws:TagKeys` | ABAC |
| `iam:PassedToService`, `iam:PermissionsBoundary` | Lock down `PassRole` and role creation |
| `kms:ViaService`, `kms:CallerAccount`, `kms:EncryptionContext:*`, `kms:RotationPeriodInDays` | Constrain key use and rotation |

## Detection stack

| Service | Key facts |
|---|---|
| CloudTrail | Without a trail only 90 days of mgmt history. One multi-Region org trail, log file validation, KMS, bucket in Log Archive ([BP](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html)) |
| GuardDuty | Foundational sources need no setup; Extended Threat Detection (attack sequences, always Critical) free; all plans except Runtime Monitoring auto-on with 30-day trial ([docs](https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html)) |
| Security Hub (unified) | Exposure findings, attack paths, OCSF; enabling it auto-enables CSPM; no third-party partner findings (those stay in CSPM) |
| Security Hub CSPM | Control checks (FSBP, CIS, NIST, PCI…); requires Config recording; 100% score ≠ passing audit |
| Config | History + rules; conformance packs bundle rules and remediation |
| Inspector | CVEs for EC2/ECR/Lambda, Code Security (SAST/SCA/IaC), continuous rescans |
| Macie / Detective | Sensitive S3 data / investigation graph over GuardDuty findings |

- Org trails are created in members even if validation fails (bad bucket/SNS/KMS policy): check `get-trail-status`. Accounts removed from the org drop out of the trail.
- Run both Security Hub and CSPM; keep CSPM for partner integrations.
- Minimum EventBridge alerts `[inference]`: GuardDuty ≥ High and every attack sequence; Critical exposure findings; root sign-in; `StopLogging`/`DeleteTrail`; new public/external Access Analyzer finding; `ConsoleLogin` without MFA; KMS `ScheduleKeyDeletion`/`DisableKey`; `PutBucketPolicy`/`DeletePublicAccessBlock`.

## Data protection

- **KMS:** CMKs $1/month, rotation default 365 days, rotation doesn't re-encrypt data; asymmetric/HMAC/custom-store keys rotate manually ([rotation](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)). The key policy is the root of trust; keep the `arn:aws:iam::<acct>:root` statement ([default policy](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html)) or the key can become unmanageable `[inference]`. Use CMKs only for cross-account sharing, separation of duties, `kms:ViaService` scoping, or crypto-shredding `[inference]`.
- **S3:** SSE-S3 default since 2023-01-05 (old objects not re-encrypted). **SSE-C disabled on new buckets since April 2026**; re-enable with `PutBucketEncryption` ([FAQ](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html)). ACLs disabled by default. Turning BPA off re-exposes existing public policies/ACLs; access-point BPA is immutable.
- S3 extras `[inference]`: `aws:SecureTransport` deny, SSE-KMS with Bucket Keys, Object Lock compliance mode for logs, CloudFront OAC instead of public buckets.
- **EBS encryption by default** is per Region and doesn't touch existing volumes ([EBS](https://docs.aws.amazon.com/ebs/latest/userguide/encryption-by-default.html)). RDS encryption is chosen at creation `[unverified here]`.
- **Secrets:** Secrets Manager ($0.40/secret/month, built-in rotation) for anything that rotates; Parameter Store (Standard free) for config. Never put secrets in Lambda env vars, CFN params without `NoEcho`, CodeBuild plaintext env, or unprotected Terraform state `[inference]`.

## Network

- Security groups: stateful, reference SGs not CIDRs, no `0.0.0.0/0` on admin ports, Session Manager over SSH `[inference]`. NACLs: stateless, mind ephemeral ports.
- [Endpoint policies](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-access.html) narrow but never override identity/resource policies; gateway endpoints (S3/DynamoDB) are free.
- Network Firewall for egress/east-west; WAF on CloudFront/ALB/API Gateway; Shield Standard free; Shield Advanced only for real DDoS exposure.
- **IMDSv2** blocks SSRF credential theft ([IMDS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-IMDS-new-instances.html)). Per Region: `aws ec2 modify-instance-metadata-defaults --http-tokens required --http-put-response-hop-limit 2` (hop limit 2 for container hosts); enforce org-wide by declarative policy.

## CI/CD: GitHub Actions → AWS via OIDC

Provider URL `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com` ([GitHub docs](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)).

```json
{ "Version": "2012-10-17", "Statement": [{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": { "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:octo-org/octo-repo:environment:prod" } } }] }
```

Subject gotchas:
- IAM **rejects** GitHub trust policies without `token.actions.githubusercontent.com:sub` or with only `*`/`?` ([IAM docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html#idp_oidc_Create_GitHub)). `repo:org/*` still lets any org repo deploy prod `[inference]`.
- **Immutable `sub` format** for repos created after 2026-07-15 (or opted in): `repo:octo-org@123456/octo-repo@456789:environment:prod`. Match whichever format the repo emits; mixed fleets need both; GHES excluded ([GitHub OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)).
- Branch-scoped: `repo:octo-org/octo-repo:ref:refs/heads/main`. PR role: `repo:octo-org/octo-repo:pull_request`, read/plan only `[inference]`.
- AWS supports only default claims (`amr`, `aud`, `email`, `oaud`, `sub`); to pin reusable workflows, customize the `sub` template to include `job_workflow_ref`.
- Using `environment:` in `sub` requires environment protection rules (reviewers, branch rules).
- Dependabot tokens carry `event_name` = `dynamic`; exclude where needed.
- `id-token: write` only mints a JWT; set it at job level on deploy jobs only `[inference]`.
- HCP Terraform OIDC: IAM requires `app.terraform.io:sub` too.

```yaml
permissions: { contents: read }
jobs:
  deploy:
    environment: prod
    permissions: { contents: read, id-token: write }
    steps:
      - uses: actions/checkout@<full-40-char-sha>
        with: { persist-credentials: false }
      - uses: aws-actions/configure-aws-credentials@<full-40-char-sha>   # v6.3.0
        with:
          role-to-assume: arn:aws:iam::111122223333:role/gha-prod-deploy
          role-session-name: gha-${{ github.run_id }}
          aws-region: eu-west-1
          role-duration-seconds: 900   # default 3600; 900-43200
```

Keep `output-credentials` false (default). Role design `[inference]`: one role per repo/env/purpose (plan vs apply), permissions boundary, deny `iam:*` except scoped `PassRole`, never chain from dev into prod.

### Supply-chain lessons

- **Trivy compromise (2026-03-19..23):** 76 of 77 `trivy-action` tags and all `setup-trivy` tags were force-pushed to credential stealers that swept AWS/GCP/Azure creds. SHA-pinned users and digest-referenced images were safe. Follow-on attack came from non-atomic rotation ([GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)). Verify binaries with `cosign verify-blob --certificate-oidc-issuer https://token.actions.githubusercontent.com ...`.
- **CodeBreach (bulletin 2026-01-15):** unanchored CodeBuild webhook `ACTOR_ID` regex. Anchor it (`^(12345|67890)$`), enable the Pull Request Comment Approval gate, or use CodeBuild-hosted Actions runners. Misconfiguration, not a CodeBuild flaw ([bulletin 2026-002](https://aws.amazon.com/security/security-bulletins/2026-002-AWS)).
- Untrusted PR builds never get deploy credentials or secrets; avoid `pull_request_target` checking out PR code `[inference]`.
- CodeBuild `[inference]`: per-project service role, no privileged mode unless building images, secrets via buildspec `secrets-manager`/`parameter-store`, CMK on cross-account artifacts, `aws:SourceArn`/`aws:SourceAccount` on service-principal trusts.
- **ECR:** enhanced scanning = Inspector (OS + language, continuous); switching modes drops scan configs ([scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)). [Managed signing](https://docs.aws.amazon.com/AmazonECR/latest/userguide/managed-signing.html) signs on push (pusher needs `signer:SignPayload`, ≤10 rules, same-Region profile); verification still needs Notation or an admission controller. Deploy by digest with tag immutability `[inference]`.

## IaC scanning

| Tool | Scans | Notes |
|---|---|---|
| cfn-guard 3.2.1 | CFN, K8s, Terraform plan JSON | `cfn-guard validate -d template.yaml -r rules/`; [Guard Hooks](https://docs.aws.amazon.com/cloudformation-cli/latest/hooks-userguide/guard-hooks.html) block at deploy |
| cdk-nag v3.0.2 | CDK apps | Needs `aws-cdk-lib` ≥ 2.257.0; `NagSuppressions` removed ([MIGRATION](https://github.com/cdklabs/cdk-nag/blob/main/MIGRATION.md)) |
| Checkov 3.4.3 | Terraform HCL/plan, CFN, K8s, Dockerfiles | `checkov -f tfplan.json` |
| Trivy v0.76.2 | `trivy config .`; tfsec is now part of Trivy | Pin and verify |
| Inspector Code Security / CT proactive controls / Prowler | Repo SAST-SCA-IaC / pre-provision CFN hooks / live CSPM | |

```ts
Validations.of(app).addPlugins(new AwsSolutionsChecks(app));   // v3, not Aspects.of(app).add(...)
Validations.of(myBucket).acknowledge({ id: 'AwsSolutions-S1', reason: 'Logs go to central bucket' });
```

Layering `[inference]`, in order: (1) pre-commit cfn-guard / Checkov / `trivy config` + secret scanning; (2) PR: same plus scans on `terraform plan` JSON and Access Analyzer `check-no-new-access` on changed IAM, SARIF to code scanning; (3) deploy: Guard Hooks / CT proactive controls; (4) runtime: Config / CSPM for drift. Suppressions need reason + owner, reviewed in PR.

## Cost traps

| Item | Price | Trap |
|---|---|---|
| CloudTrail extra mgmt copies | $2.00/100k | Org + account + CT trails = 2–3× |
| CloudTrail data events | $0.10/100k | Hot S3 buckets cost thousands/month |
| Config items | $0.003 continuous / $0.012 periodic | Chatty ENI/EBS types; use periodic or exclude |
| KMS CMK | $1/key/month | Per-tenant keys; SSE-KMS without Bucket Keys |
| Interface endpoints | $0.01/h per ENI per AZ + $0.01/GB | Services × AZs × VPCs; centralize `[inference]` |
| Network Firewall | $0.395/h per endpoint + $0.065/GB | Per AZ per VPC; centralize in inspection VPC |
| Shield Advanced | $3,000/month, 1-yr | Needs Business/Enterprise support |
| GuardDuty | 30-day trial | Bill appears after trial (S3, EKS on busy accounts) |

## Debug

| Symptom | Cause | Fix |
|---|---|---|
| IAM refuses to save GitHub OIDC trust policy | Missing `sub` condition or wildcard-only `sub` | Add `StringEquals` on `aud` and a repo-specific `sub` |
| `AssumeRoleWithWebIdentity` denied on a new repo | Repo emits immutable `owner@id/repo@id` `sub` | Match the format the repo emits |
| `AccessDenied` despite allow policy | Explicit deny somewhere (SCP/RCP/boundary) | Read the error wording ("explicit deny in a service control policy") `[inference]` |
| Vendor or CloudFront access broke after RCP | Identity perimeter has no exception | Add `aws:PrincipalAccount` or `aws:SourceArn`/`aws:SourceAccount` exceptions |
| Org trail "created" but no logs | Bucket/SNS/KMS policy invalid | Run `get-trail-status`, fix policy |
| App writing SSE-C to a new bucket fails | SSE-C disabled since April 2026 | `PutBucketEncryption` to re-enable |
| CloudTrail bill doubled | Duplicate mgmt-event trails | Keep one copy |
| Control Tower controls in unknown state | CT-managed resource hand-edited | Don't modify CT resources |
| ECR scan configs vanished | Switched basic ↔ enhanced scanning | Reconfigure after switching |

## Incident response first steps

Prepare: pre-provisioned break-glass and forensics roles in every account, playbooks ([aws-customer-playbook-framework](https://github.com/aws-samples/aws-customer-playbook-framework)), game days. [AWS Security Incident Response](https://docs.aws.amazon.com/security-ir/latest/userguide/what-is.html) triages GuardDuty and integrated threat findings, not posture findings.

Leaked access key `[inference]`:
1. Identify the principal (CloudTrail, `aws iam get-access-key-last-used`), then **deactivate** the key (don't delete yet); for roles, "Revoke active sessions" (adds an `aws:TokenIssueTime` deny).
2. Search CloudTrail for new users/keys/roles, `CreateLoginProfile`, odd-Region Lambda/EC2 launches, `PutBucketPolicy`; remove persistence.
3. Rotate dependent secrets, check the bill for crypto-mining, open a Support case.

Compromised EC2 `[inference]`: swap in a no-ingress/no-egress SG (tracked connections may persist), detach from ASG/ELB, snapshot EBS and capture memory before stopping, tag with case ID, analyze in a forensics account.

## Hardening checklist

| Priority | Items (in order) |
|---|---|
| **P0** day 0 | Org with all features, management account holds no workloads; management root MFA + no keys, centralized root access, member root creds removed; landing zone (Log Archive, Security Tooling, Workloads, Sandbox); Identity Center + IdP (SCIM), group permission sets, 1 h admin sessions, no IAM users; one org CloudTrail (multi-Region, validation, KMS, Object Lock bucket in Log Archive); baseline SCPs (leave-org, protect security services/logs, region allow-list, deny member root); org-level S3 BPA; Budgets + cost anomaly alert `[inference]` |
| **P1** week 1 | Delegated admin in Security Tooling with auto-enable; GuardDuty org-wide (S3 Protection, Runtime Monitoring for EC2/EKS/ECS); Security Hub Essentials + CSPM (FSBP, CIS) with aggregator Region; Access Analyzer external/unused/internal; EBS default encryption + IMDSv2 in every Region; EventBridge alerting; GitHub OIDC roles with `aud` + `sub` and delete CI access keys |
| **P2** month 1 | RCPs (identity perimeter, TLS-only) tested in sandbox; permissions boundaries + Access Analyzer checks in PRs; policy-as-code in every IaC repo + Guard Hooks / proactive controls; ECR enhanced scanning, tag immutability, managed signing, deploy by digest; Secrets Manager with rotation; private subnets, gateway endpoints, SG review, WAF on public entry; Macie automated discovery |
| **P3** ongoing | IR playbooks, forensics roles, quarterly game day; quarterly unused-access, key-policy, SCP/RCP and security-cost reviews; Well-Architected Security pillar review per workload (pillar last revised 2024-11-06) |

## Do / Avoid

**Do**
- Write policies with explicit `Resource` ARNs and conditions; run `validate-policy` on each.
- Add `aws:SourceArn` + `aws:SourceAccount` to every grant to a service principal.
- Scope OIDC trust to `repo:<org>/<repo>:environment:<env>` (or immutable form) with protection rules.
- Pin actions to SHAs, images to digests; verify Sigstore/Notation signatures on security tools.
- Keep a break-glass role excluded from SCP denies via `aws:PrincipalArn`, and alarm on its use.
- Treat CI logs from a supply-chain exposure window as compromised; rotate all reachable secrets.
- Set `HttpTokens=required`, hop limit 2 on container hosts.
- Estimate Config, CloudTrail, Network Firewall and endpoint costs before org-wide enablement.

**Avoid**
- IAM users or access keys for humans or CI; `AdministratorAccess` on CI roles.
- `repo:org/*` or `*` subjects; `Principal: "*"` without org/VPC/source conditions.
- Workloads or daily Identity Center use in the management account.
- Duplicate management-event trails.
- Removing the account-root statement from KMS key policies.
- `pull_request_target` with PR checkout and secrets/OIDC; unanchored CodeBuild webhook regexes.
- CSPM scores as audit evidence; hand-editing Control Tower resources; SSE-C in new designs.
- cdk-nag v2 APIs (`Aspects.of(...)`, `NagSuppressions`) on `aws-cdk-lib` ≥ 2.257.0.

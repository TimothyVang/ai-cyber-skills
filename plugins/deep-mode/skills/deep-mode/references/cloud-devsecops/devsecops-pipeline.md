# Cross-cloud DevSecOps pipeline

Read when designing, reviewing, debugging or securing a CI/CD pipeline or cloud deployment on AWS, Azure or GCP: scanner gates, GitHub Actions hardening, CI-to-cloud OIDC, SBOM/signing/provenance, container and Kubernetes hardening, policy as code, CSPM. State as of 2026-11-11. Full report: https://github.com/TimothyVang/cloud-devsecops/blob/main/research/devsecops-cross-cloud.md

Per-cloud details: `aws.md`, `azure.md`, `gcp.md`. Local testing: `local-emulators.md`. General tooling: `devops-tools.md`.

## 2025–2026 changes that break assumptions

- Security tooling is privileged supply chain. TeamPCP (2026-03-19) published malicious Trivy v0.69.4 and force-pushed 76/77 `trivy-action` tags and all `setup-trivy` tags ([CVE-2026-33634](https://nvd.nist.gov/vuln/detail/cve-2026-33634), CISA KEV). SHA-pinned workflows were safe. Safe: Trivy 0.69.2/0.69.3, trivy-action 0.35.0+, setup-trivy 0.2.6. The same actor hijacked 35 KICS action tags on 2026-03-23 ([Wiz](https://www.wiz.io/blog/teampcp-attack-kics-github-action)).
- GitHub Actions workflow lockfiles GA 2026-10-28 (`.github/workflows/actions.lock`, `gh actions-lock`, "Require lockfile" policy): pins transitive actions and records `owner_id`/`repo_id` ([docs](https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles)). Reusable workflows are not covered: pin them by SHA.
- `pull_request_target` blocked by default in public repos from 2026-12-02 (not private/internal/GHES) unless an Actions event policy allows it ([changelog](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/)). `actions/checkout` refuses fork heads under it unless `allow-unsafe-pr-checkout: true`.
- Kyverno 1.19 deprecates `ClusterPolicy`/`Policy`/`CleanupPolicy`; removal planned in v1.20 (~Nov 2026). Use CEL types `ValidatingPolicy`, `MutatingPolicy`, `GeneratingPolicy`, `ImageValidatingPolicy`, `DeletingPolicy` ([blog](https://main.kyverno.io/blog/2026/08/20/announcing-kyverno-release-1.19/)).
- Cosign v3 turns on new bundle format, trusted root and signing config by default; v4 will drop legacy flags ([Sigstore](https://blog.sigstore.dev/cosign-3-0-available/)).
- Terrascan archived; tfsec superseded by Trivy. Dependabot applies a default 3-day cooldown to version (not security) updates.

## Standards map

| Framework | Version | Use it to |
|---|---|---|
| [OWASP Top 10](https://top10.owasp.org/2025/0x00_2025-Introduction) | 2025 (adds A03 Supply Chain Failures, A10 Mishandling of Exceptional Conditions) | Name app risk classes; A10 means fail closed in authz/policy paths |
| OWASP ASVS | 5.0.0, ~350 reqs, 17 chapters, L1–L3 | Testable security requirements |
| [OWASP SAMM](https://owaspsamm.org/model/) | v2: Governance, Design, Implementation, Verification, Operations | Program maturity roadmap |
| [OWASP CI/CD Top 10](https://owasp.org/www-project-top-10-ci-cd-security-risks/) | CICD-SEC-1…10 | Threat-model a CI/CD system |
| NIST SSDF SP 800-218 | 1.1 final; [1.2 draft](https://csrc.nist.gov/pubs/sp/800/218/r1/ipd) (Dec 2025, no final) | PO/PS/PW/RV vocabulary for attestation; exact 1.2 additions `[unverified]` |
| [NIST SP 800-204D](https://csrc.nist.gov/pubs/sp/800/204/d/final) | Final, Feb 2024 | Map supply-chain controls into CI/CD |
| [CISA Secure by Design](https://www.cisa.gov/securebydesign/pledge) | 7-goal pledge | No default creds in IaC/Helm, MFA, audit logs on by default |
| [SLSA](https://slsa.dev/spec/v1.2) | v1.2: Build L0–L3, Source L1–L4 | Grade build/source integrity |
| [OpenSSF Scorecard](https://github.com/ossf/scorecard) | v5.6.0 | Repo hygiene scoring |

CI/CD Top 10 → control:

| ID | Risk | Control |
|---|---|---|
| SEC-1 | Flow control | Rulesets, required reviews/checks, prod environment protection |
| SEC-2 | IAM | SSO/MFA, remove stale accounts |
| SEC-3 | Dependency chain abuse | Lockfiles, registry scoping, cooldowns |
| SEC-4 | Poisoned pipeline execution | No `pull_request_target` + PR checkout; CODEOWNERS on `.github/workflows` |
| SEC-5 | Pipeline access controls | Per-job `permissions:`, environment secrets, OIDC `sub` conditions |
| SEC-6 | Credential hygiene | OIDC over static keys, secret scanning, push protection |
| SEC-7 | Insecure system config | Ephemeral runners, no self-hosted on public repos |
| SEC-8 | Ungoverned 3rd-party services | Allowed-actions policy, App scope review |
| SEC-9 | Artifact integrity | Signing, provenance, verify at deploy/admission |
| SEC-10 | Logging/visibility | Audit log streaming, egress telemetry |

## Reference pipeline

Gate on risk (severity + KEV/EPSS + reachability), baseline the backlog, fail closed when a scanner produces no report, and keep time-boxed exceptions ([OWASP gates](https://owasp.github.io/DevSecOpsGuideline/2-Process/2-3-Build/2-3-5-Security-Gates/)). Adoption order from zero: secrets → SCA → branch protection + SAST → IaC → container → DAST → SBOM + signing. Rollout: warn-only 1–2 weeks → block Critical → block Critical+High.

| # | Stage | Tools | Fail threshold |
|---|---|---|---|
| 0 | Pre-commit | gitleaks hook, Semgrep/Opengrep IDE, actionlint | Advisory; CI repeats it |
| 1 | Pipeline self-check (PR) | zizmor, actionlint, stale-lock check (flag `[unverified]`) | Any high zizmor finding, unpinned action, stale lockfile |
| 2 | Secrets | TruffleHog `--results=verified,unknown` or gitleaks; push protection | Any verified/unknown secret |
| 3 | SAST (PR) | CodeQL and/or Semgrep/Opengrep diff-aware | New High/Critical (CodeQL via ruleset) |
| 4 | SCA (PR) | Trivy fs / OSV-Scanner / Grype | Critical/High with fix (`--ignore-unfixed`); always KEV `[inference]`; license denylist |
| 5 | IaC + policy | Trivy config or Checkov on HCL and plan JSON; Conftest/Kyverno CLI | High/Critical misconfig; any policy `deny` |
| 6 | Build (main) | Ephemeral hosted runner, harden-runner, base image by digest | Unexpected egress |
| 7 | Image scan | Trivy image by digest or Grype | Critical/High fixable; root user (policy) |
| 8 | SBOM + provenance + sign | Syft → `actions/attest` → `cosign sign` keyless | Any failure; never `continue-on-error` |
| 9 | Deploy staging | Per-env OIDC role; `gh attestation verify`/`cosign verify`; admission | Verification fails → abort |
| 10 | DAST | ZAP baseline, `fail_action: true`, rules tsv | Rules marked FAIL |
| 11 | Prod | Environment with required reviewers | Promote the same digest; no rebuild |
| 12 | Continuous | Registry re-scan, Prowler, kube-bench/Kubescape, Falco, weekly Scorecard | Alert; SLA e.g. Critical 7d, High 30d |

CodeQL `analyze` uploads SARIF but does not fail the job: enforce with a ruleset "code scanning results" rule.

## Example GitHub Actions workflow (excerpt)

SHAs resolved 2026-11-11; re-resolve before use or use `gh actions-lock`. The full workflow (all stages, ZAP, staging deploy) is in the report §8.1.

```yaml
on: { pull_request: {}, push: { branches: [main] } }
permissions: {}                       # deny-all; each job opts in
jobs:
  sca-iac:
    runs-on: ubuntu-latest
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { persist-credentials: false }
      - uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
        with: { version: v0.76.2, scan-type: fs, severity: 'CRITICAL,HIGH', ignore-unfixed: true, exit-code: '1' }
  build-sign:
    if: github.event_name == 'push'
    needs: [sca-iac]
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write, id-token: write, attestations: write }
    steps:
      - uses: step-security/harden-runner@1d88384fd173af6ecb012dfd0264a306b711241a # v2.22.4
        with: { egress-policy: audit }   # then block + allowed-endpoints
      # checkout, buildx, login, build-push (id: build) ...
      - uses: anchore/sbom-action@66cbf4bc1f1c0d2edc94016e65bc221b6bb0ad6c # v0.24.3
        with: { image: "${{ env.IMAGE }}@${{ steps.build.outputs.digest }}", format: cyclonedx-json, output-file: sbom.cdx.json }
      - uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
        with: { subject-name: "${{ env.IMAGE }}", subject-digest: "${{ steps.build.outputs.digest }}", push-to-registry: true }
      - uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
        with: { subject-name: "${{ env.IMAGE }}", subject-digest: "${{ steps.build.outputs.digest }}", sbom-path: sbom.cdx.json, push-to-registry: true }
      - uses: sigstore/cosign-installer@756fe2d284c7292c4e9b62c8a28f1e5629c59532 # v4.1.3
      - run: cosign sign --yes "${IMAGE}@${DIGEST}"
        env: { DIGEST: "${{ steps.build.outputs.digest }}" }
  deploy-staging:
    needs: build-sign
    environment: staging              # OIDC sub = repo:ORG/REPO:environment:staging
    runs-on: ubuntu-latest
    permissions: { contents: read, id-token: write, attestations: read }
    steps:
      - run: gh attestation verify "oci://${IMAGE}@${DIGEST}" -R "${GITHUB_REPOSITORY}"
        env: { GH_TOKEN: "${{ github.token }}", DIGEST: "${{ needs.build-sign.outputs.digest }}" }
      - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
        with: { role-to-assume: "arn:aws:iam::123456789012:role/gha-deploy-staging", aws-region: eu-west-1 }
```

- Pin the scanner binary (`version:`) as well as the action SHA.
- Avoid `gitleaks-action` in org repos (needs a license key); the gitleaks binary is fine.
- trivy-action `scanners`/`scan-ref` inputs for config scans: `[unverified]` on v0.36.

## CI-to-cloud OIDC federation

1. Grant `id-token: write` only to the deploying job; put it in an `environment:`.
2. Trust policy matches issuer, `aud` and `sub` exactly with `StringEquals`. AWS `aud` is `sts.amazonaws.com`; AWS does not support custom OIDC claims ([GitHub OIDC](https://docs.github.com/en/actions/reference/security/oidc)).
3. `sub` form depends on the job: environment jobs get `repo:ORG/REPO:environment:NAME`, not `repo:ORG/REPO:ref:refs/heads/main`.
4. Never `StringLike` with `repo:ORG/*` for deploy roles `[inference]`. One role per environment.
5. Azure (federated identity credential) and GCP (Workload Identity Federation with an `attribute.repository` condition) follow the same exact-match model.

```json
"Condition": { "StringEquals": {
  "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
  "token.actions.githubusercontent.com:sub": "repo:my-org/app:environment:staging" } }
```

## Supply chain: SBOM, signing, provenance

- On GitHub, artifact attestations + a reusable workflow is the documented path to SLSA Build L3 ([docs](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/increase-security-rating)). Prefer `actions/attest`; `attest-build-provenance` v4 is a wrapper; `slsa-github-generator` last released 2025-02.
- Attestation permissions: `id-token: write`, `contents: read`, `attestations: write`, plus `packages: write` for images. Image subject: `subject-name` without tag + `subject-digest`.
- Private/internal repos need GitHub Enterprise Cloud for attestations.
- Verify SBOM attestation: `gh attestation verify oci://... -R ORG/REPO --predicate-type https://spdx.dev/Document/v2.3`.
- Keyless cosign verify must pin identity and issuer, or any Fulcio cert passes ([doc](https://github.com/sigstore/cosign/blob/main/doc/cosign_verify.md)). Use regexp forms only anchored. `verify-blob` prefers `--bundle`.

```bash
cosign verify ghcr.io/org/app@sha256:<digest> \
  --certificate-identity "https://github.com/org/repo/.github/workflows/release.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

- SBOM formats: CycloneDX 1.7 (ECMA-424 2nd ed., native VEX, CBOM); SPDX 3.0.1 (ISO/IEC 5962:2021 = SPDX 2.2.1). GitHub examples still use the SPDX 2.3 predicate.
- Generate the SBOM from the built image (`syft <image> -o cyclonedx-json`), attest it to the digest, scan it downstream (`grype sbom:./sbom.json`) `[inference]`.

## Scanner and tool comparison (GitHub API, 2026-11-11)

| Category | Tool | License | Latest | Status |
|---|---|---|---|---|
| Vuln/SCA/IaC/SBOM | Trivy | Apache-2.0 | v0.76.2 | Active; compromised 2026-03, pin by SHA |
| Vuln | Grype | Apache-2.0 | v0.121.3 | Active; EPSS/KEV, OpenVEX; `--fail-on` `[unverified]` |
| Vuln/SCA | OSV-Scanner | Apache-2.0 | v2.7.1 | Active; reachability, licenses; `fix` runs scripts |
| SBOM | Syft / cdxgen | Apache-2.0 | v1.57.1 / v13.7.0 | Active |
| SAST | Semgrep CE | LGPL-2.1; rules under non-OSI Semgrep Rules License | v1.185.0 | Active, open-core |
| SAST | Opengrep | LGPL-2.1 | v1.33.1 | Active fork (from 1.100.0) |
| SAST | CodeQL | Queries MIT; CLI OSS/academic only | 2.27.4 | Private repos need Code Security ($30/committer/mo) |
| Secrets | gitleaks | MIT | v8.30.1 | Active; `detect`/`protect` deprecated → `git`/`dir` |
| Secrets | TruffleHog | AGPL-3.0 | v3.99.8 | Active; live verification |
| IaC | Checkov | Apache-2.0 | 3.4.3 | Active; plan JSON; severity gating may need Prisma metadata `[unverified]` |
| IaC | KICS | Apache-2.0 | v2.2.1 | Active; action hijacked 2026-03 |
| IaC | tfsec / Terrascan | MIT / Apache-2.0 | — | Superseded by Trivy / archived: do not use |
| Policy | OPA, Conftest, Gatekeeper, Kyverno | Apache-2.0 | v1.22.3, v0.71.1, v3.23.1, v1.19.2 | Active |
| K8s | kube-bench, Kubescape, Falco | Apache-2.0 | v0.16.0, v4.0.20, 0.45.2 | Active |
| DAST | ZAP | Apache-2.0 | v2.17.0 | Active (Checkmarx-backed) |
| Signing | cosign, Rekor | Apache-2.0 | v3.1.4, v1.6.1 | Active |
| CI | harden-runner, zizmor, actionlint | Apache-2.0, MIT, MIT | v2.22.4, v1.32.0, v1.7.12 | Active |
| Deps | Dependabot / Renovate | MIT / AGPL-3.0 | — | Active |
| CSPM | Prowler | Apache-2.0 | 5.48.0 | Very active, recommended |
| CSPM | ScoutSuite / CloudSploit | GPL-2.0 / GPL-3.0 | 5.14.0 / v3.9.0 | Dormant / low cadence |

## Containers and Kubernetes

- Base: distroless (`nonroot` tags, no shell), Chainguard/Wolfi, or `scratch`. Pin by digest; never ship `debug` tags. Multi-stage builds; BuildKit `--mount=type=secret`, never `ARG` for secrets.
- [PSS](https://kubernetes.io/docs/concepts/security/pod-security-standards/) `restricted` requires `runAsNonRoot`, non-zero UID, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, seccomp `RuntimeDefault`. It does not require `readOnlyRootFilesystem`: enforce that by policy.
- Label namespaces `pod-security.kubernetes.io/<mode>: <level>`; roll out `warn`+`audit` before `enforce`; pin `enforce-version`.

```yaml
securityContext: { runAsNonRoot: true, runAsUser: 65532, seccompProfile: { type: RuntimeDefault } }
containers:
  - name: app
    image: ghcr.io/my-org/app@sha256:<digest>
    securityContext: { allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, capabilities: { drop: ["ALL"] } }
    volumeMounts: [{ name: tmp, mountPath: /tmp }]
volumes: [{ name: tmp, emptyDir: {} }]
automountServiceAccountToken: false
```

- RBAC: no `cluster-admin` for workloads, no wildcards; treat `escalate`, `bind`, `impersonate`, `pods/exec`, `get secrets` as privileged.
- NetworkPolicy: default-deny ingress and egress per namespace, then allow DNS and needed flows; requires an enforcing CNI.
- kube-bench/Kubescape for CIS; managed control planes allow worker checks only. CIS version used by kube-bench v0.16.0 `[unverified]`.

## Policy as code

- Run the same policy in CI (Conftest, `kyverno` CLI) and at admission (Gatekeeper, Kyverno, ValidatingAdmissionPolicy) `[inference]`.
- Kyverno: write `ImageValidatingPolicy` etc. Storage version is `v1beta1` on 1.19, `v1` on 1.20. Gatekeeper can generate native VAP (CEL).
- Rego uses v1 syntax (`import rego.v1`, `deny contains msg if`); `conftest test k8s/*.yaml` exits non-zero on `deny`.

## CI hardening rules

- `permissions: {}` at top; repos created before 2023-02-02 may default to read/write tokens.
- Pin actions by full SHA with version comment or lockfile; enforce via "Require full-length SHA"/"Require lockfile" policy. In lockfile review, a changed `owner_id`/`repo_id` means a different repo: investigate; never `--accept-moved` in automation.
- Untrusted event data (`${{ github.event.* }}`) goes through `env:` and is quoted, never inlined in `run:`.
- `pull_request_target`/`workflow_run`: default to `pull_request`; never execute PR code or trust `workflow_run` artifacts ([docs](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)).
- `persist-credentials: false` on checkout; CODEOWNERS on `.github/workflows/`; disable "Allow GitHub Actions to create and approve pull requests".
- Self-hosted runners: almost never on public repos; JIT/ephemeral, runner groups, no metadata-service access.
- [harden-runner](https://github.com/step-security/harden-runner): `audit` then `block`. Free tier covers public repos on GitHub-hosted runners only; silent no-op on self-hosted without Enterprise; audit-only on Windows/macOS.
- zizmor + actionlint on every PR; CodeQL also analyzes workflows. Scorecard (`ossf/scorecard-action` v2.5.0) weekly: Dangerous-Workflow, Pinned-Dependencies, Token-Permissions, Signed-Releases, Branch-Protection, etc.

## Runtime and CSPM

- CNAPP = CSPM (control-plane misconfig) + CWPP (workload) + CIEM (entitlements) + KSPM (K8s posture).
- Run [Prowler](https://github.com/prowler-cloud/prowler) on a schedule with read-only roles (AWS `SecurityAudit`+`ViewOnlyAccess`, Azure `Reader`, GCP `roles/viewer`+`roles/iam.securityReviewer`); export JSON/OCSF/SARIF to one store; gate promotion on new criticals `[inference]`.
- Falco (CNCF graduated) watches syscalls and K8s audit: shells in containers, writes under `/etc`, unexpected egress; ship via Falcosidekick to SIEM.
- ZAP baseline on every staging deploy; full active scans only against disposable environments.

## Prioritized hardening checklist

- P0: delete static cloud keys; OIDC with exact `aud`+`sub`. `permissions: {}` per workflow. SHA/lockfile pins for actions and scanner binaries. Secret scanning + push protection; rotate leaked secrets. No `pull_request_target` running PR code.
- P1: SCA + SAST + IaC gates on new fixable High/Critical; zizmor + CODEOWNERS on workflows; environments with required reviewers; harden-runner audit → block.
- P2: SBOM + provenance + cosign; verify at deploy and admission; promote digests; PSS restricted + rootfs policy + default-deny NetworkPolicy.
- P3: DAST, scheduled Prowler, kube-bench/Kubescape, Falco, weekly Scorecard, finding SLAs.

## Debug

| Symptom | Cause | Fix |
|---|---|---|
| Fork-PR workflow stops running after 2026-12-02 | `pull_request_target` default block | Move to `pull_request` or allow via Actions event policy |
| "lockfile missing pin for X" | Local `./` action uses an unlocked action | `gh actions-lock --migrate-local-actions` |
| `AssumeRoleWithWebIdentity` AccessDenied | Token `sub` form (environment vs ref) or `aud` mismatch | Match the trust policy to the environment form |
| `attestations: write` errors in private repo | Plan lacks attestations | Needs GitHub Enterprise Cloud |
| cosign verify fails after v3 upgrade | Bundle-format default changed | Check signer's cosign version and `--new-bundle-format` |
| Pods rejected after namespace label | Missing seccomp, `drop: [ALL]`, or root UID | Read `warn` output first, fix securityContext |
| Trivy install script fails NXDOMAIN | `get.trivy.dev` issue ([#11537](https://github.com/aquasecurity/trivy/issues/11537)) `[unverified: current state]` | Pin binary another way; Grype/OSV as second opinion |
| CodeQL finds issues but PR merges | `analyze` does not fail the job | Ruleset "code scanning results" rule |

## Do / Avoid

Do:
- Grant `id-token: write` only to jobs that federate or sign.
- Gate on new fixable High/Critical or KEV; baseline the rest; fail closed on missing reports.
- Build once, promote the digest, verify signature/provenance at deploy and admission.
- Keep Dependabot cooldown / Renovate `minimumReleaseAge`; let security updates through.
- Scan both Terraform HCL and `terraform show -json` plan output.

Avoid:
- Tag-only pins (`@v3`, `@main`, `:latest`) for actions, images or scanners.
- `continue-on-error: true` or `|| true` on security steps outside a dated rollout.
- Blocking on raw counts or unfixable Mediums; the gate gets disabled.
- Terrascan, tfsec, ScoutSuite as primary tools; new Kyverno `ClusterPolicy`.
- `cosign verify` without identity and issuer; legacy `.sig` tags in new code.
- Treating a deleted secret line as fixed; running OSV-Scanner `fix` or build scripts on untrusted repos.
- `ARG`/`ENV` secrets, root containers, `privileged: true` or `hostPath` without written justification.

## Gaps and staleness

`pull_request_target` date may slip; Kyverno 1.20 and cosign v4 will change syntax; SSDF 1.2 still draft; lockfile edge cases open (SHA policy vs locked actions in reusable workflows); action SHAs above go stale every release.

# Local Cloud Emulators (Floci, LocalStack, moto, Azurite, Google, Cosmos)

Read when testing IaC (Terraform/OpenTofu, CDK, Bicep), SDK code, or CI pipelines against AWS, Azure, GCP or OCI without touching a real account; when choosing or migrating a local emulator; or when a local run "passed" and you must decide whether to trust it. Full report: https://github.com/TimothyVang/cloud-devsecops/blob/main/research/floci-local-cloud-emulators.md

## When to test locally first

- Test locally first for every IaC plan/apply/destroy loop, SDK integration test, and CI job that creates resources. It is free, needs no account, and cannot bill or break production if wired correctly.
- Local green is necessary, not sufficient. Every emulator documents gaps (IAM coverage, consistency, RU/s, error text). Always finish with a smoke run in a real **sandbox** account using short-lived CI OIDC credentials, never long-lived keys [inference].
- Use moto for in-process Python unit tests; Floci for container-level integration and IaC loops; Google's emulators for Spanner/Bigtable; the Cosmos emulator only when Cosmos-specific semantics matter [inference].

## Floci family

All MIT, no account, no auth token, no feature gates ([floci README](https://github.com/floci-io/floci); [floci-cli README](https://github.com/floci-io/floci-cli)).

| Emulator | Cloud | Port | Image | Env prefix | Health |
|---|---|:---:|---|---|---|
| `floci` | AWS | 4566 | `floci/floci` | `FLOCI_` | `/_floci/health` |
| `floci-az` | Azure | 4577 | `floci/floci-az` | `FLOCI_AZ_` | `/_floci/health` |
| `floci-gcp` | GCP | 4588 | `floci/floci-gcp` | `FLOCI_GCP_` | `/_floci-gcp/health` (also `/health`) |
| `floci-oci` | OCI | 4599 | `floci/floci-oci` | `FLOCI_OCI_` | `/_floci-oci/health` |
| `floci-cli` | lifecycle for all | n/a | binary / `floci.jar` | `FLOCI_*` | n/a |

### AWS fidelity tiers

Check the tier before trusting a result (Floci CLI skill, AWS reference: [floci-cli skills](https://github.com/floci-io/floci-cli/tree/main/skills/floci)):

| Tier | Services | Trust for |
|---|---|---|
| Real containers (need Docker socket) | Lambda, RDS (Postgres/MySQL/MariaDB), ElastiCache (Valkey), MSK (Redpanda), EKS (k3s), OpenSearch, Neptune, DocumentDB, Amazon MQ, MWAA, CodeBuild, EC2 (containers + IMDS) | Real behaviour |
| In-process, full behaviour | S3, DynamoDB, SQS, SNS, IAM, STS, KMS, Secrets Manager, SSM, EventBridge, Step Functions, Kinesis, CloudFormation, API Gateway, Cognito | Integration tests |
| Canned/stub | Bedrock Runtime, Textract, Transcribe, Signer, FIS (no faults), QuickSight | Wiring/control plane only, never output |

**Other clouds:** floci-az covers Blob/Queue/Table (Azurite connection string works), Key Vault, App Config, Cosmos NoSQL, SQL, Event Hubs, Service Bus, Functions, AKS, ARM incl. Bicep, Azure Policy (on writes), Entra ID, Managed Identity ([floci-az](https://github.com/floci-io/floci-az)). floci-gcp serves gRPC+REST on one port: GCS, Firestore, Datastore, Pub/Sub, Secret Manager, KMS, IAM/STS, Cloud Run and Cloud SQL (real Docker), BigQuery (DuckDB), GKE ([floci-gcp](https://github.com/floci-io/floci-gcp)). floci-oci: Identity, Object Storage, Vault/KMS, Functions, OKE, Postgres; Oracle has no official emulator ([floci-oci](https://github.com/floci-io/floci-oci)).

## Install

| Path | Command | Notes |
|---|---|---|
| CLI (recommended) | `brew install floci-io/floci/floci`, `curl -fsSL https://floci.io/install.sh \| sh`, `iwr https://floci.io/install.ps1 \| iex`, or `java -jar floci.jar` (Java 25+) | Manages lifecycle only; does not wrap `aws`/`az`/`gcloud`/`oci` |
| Docker / Compose | `image: floci/floci:2.4.0`, `ports: ["127.0.0.1:4566:4566"]` | Docker 23.0+ and compose v2 ([installation doc](https://github.com/floci-io/floci/blob/main/docs/getting-started/installation.md)) |
| Native binary | `floci-aws-<os>-<arch>` from Releases | Verify via `sha256sums.txt`, cosign `*.sigstore.json` or `gh attestation verify`; Linux needs glibc >= 2.34 (no Alpine/RHEL 8/AL2) |
| Kubernetes | `helm install floci ./charts/floci -n floci --create-namespace --wait` | Lambdas run as pods |

- Native binary without Docker: RDS, ElastiCache, OpenSearch, EKS, MSK become control-plane only; Lambda, ECS, CodeBuild, Athena, ECR **fail** (startup warning lists them).
- Tags: `latest`, pinned `x.y.z` (CI), `-compat` (AWS CLI + boto3 for init scripts), `-baseline` (ARM64 no LSE), `nightly`. Images lack curl/wget: use built-in healthcheck via `docker compose up -d --wait`.
- Compose port mappings needed: ElastiCache `6379-6399`, MemoryDB `6400-6419`, RDS `7001-7099`, Neptune `8182-8282`, MWAA `8700-8799` ([ports doc](https://github.com/floci-io/floci/blob/main/docs/configuration/ports.md)).

## Env setup per cloud

| Cloud | Wire-up | Gotcha |
|---|---|---|
| AWS | `eval "$(floci aws env -o text)"` sets `AWS_ENDPOINT_URL=http://localhost.floci.io:4566`, `test`/`test`, `us-east-1` | Never add `-q` (suppresses exports). `--profile <real>` can override the endpoint. Some SDKs skip `AWS_ENDPOINT_URL` for SQS |
| Azure | `floci az setup && eval "$(floci az env -o text)"` | Without `setup`, `az` control-plane commands hit **real Azure** |
| GCP | `eval "$(floci gcp env -o text)"` sets `*_EMULATOR_HOST=localhost:4588` | `gcloud` **ignores** `*_EMULATOR_HOST`; set `CLOUDSDK_API_ENDPOINT_OVERRIDES_<API>` |
| OCI | `floci oci setup` writes `~/.oci/floci_key.pem` and a `[FLOCI]` profile | Never point the `-compat` image's public key at real OCI |

- SDKs (AWS): `endpointOverride`/`endpoint_url`/`BaseEndpoint`; S3 path-style unless the host is `localhost.floci.io`.
- Set `FLOCI_HOSTNAME` (AWS), `FLOCI_AZ_HOSTNAME`, or `FLOCI_GCP_HOSTNAME`+`FLOCI_GCP_BASE_URL` when another container consumes returned URLs (SQS `QueueUrl`, presigned URLs).
- Python Secret Manager ignores `SECRET_MANAGER_EMULATOR_HOST`: use `transport="rest"`, `AnonymousCredentials()`, `client_options={"api_endpoint": "http://localhost:4588"}` (Floci CLI skill, GCP reference: [floci-cli skills](https://github.com/floci-io/floci-cli/tree/main/skills/floci)).
- Azure TLS (`FLOCI_AZ_TLS_ENABLED=true`, cert at `/_floci/tls-cert`) is required for `az` control plane, Cosmos Java SDK, and Terraform `azurerm`. The CLI starts floci-az with TLS on.
- PowerShell: `floci <tree> env --shell powershell | Invoke-Expression`. Multi-account AWS: a 12-digit `AWS_ACCESS_KEY_ID` becomes the account ID.

## Strictness and IAM enforcement

Default posture is permissive: no signature checks, no IAM, in-memory state. A green run proves nothing about least privilege unless enforcement was on, and even then coverage is partial ([env vars](https://github.com/floci-io/floci/blob/main/docs/configuration/environment-variables.md)).

| Switch | Effect |
|---|---|
| `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true` | AWS IAM policy evaluator (SCP → explicit Deny → Allow → session → boundary → implicit deny) |
| `FLOCI_AUTH_VALIDATE_SIGNATURES=true` | Verify SigV4 only, no policy |
| `FLOCI_SERVICES_S3_ENFORCE_AUTH=true` | S3 public/private reads |
| `FLOCI_PARTITIONS_STRICT=true` | Reject services absent from the partition |
| `FLOCI_NETWORK_SECURITY_GROUP_ENFORCEMENT_ENABLED=true` | nftables SG filtering for EC2/ECS `awsvpc` |
| `FLOCI_SERVICES_EC2_ENFORCE_VCPU_QUOTAS=true` | vCPU quota admission |
| `FLOCI_GCP_SERVICES_IAM_AUTHORIZATION_MODE=enforce` | GCP allow policies for Resource Manager, Cloud Run v2 services, Secret Manager, Pub/Sub, Scheduler, Logging sinks, IAM, GCS REST only |
| `FLOCI_AZ_PARITY=compat\|azure\|strict` | `strict` refuses unknown subscriptions/resource groups |
| `FLOCI_OCI_AUTH_REQUIRE_SIGNATURE=true` | Reject unsigned (signatures never verified) |

- Confirm AWS enforcement from the banner: `IAM: policy enforcement enabled`. Misspelled vars (e.g. `FLOCI_IAM_STRICT_VALIDATION`) are silently ignored ([iam.md](https://github.com/floci-io/floci/blob/main/docs/services/iam.md)).
- Read iam.md "Bypass rules" and "Unsigned requests" before treating a denial as proof [inference]. Unenforced: GCP Cloud Run jobs, GCS ACLs/gRPC; Azure Policy only on writes; OCI policies not evaluated. Name uncovered services in reports. Binding beyond `127.0.0.1` needs `FLOCI_SECURITY_ALLOW_UNSAFE_NETWORK_EXPOSURE=true`; anyone reaching the port can use the fake creds.

## Persistence

- `FLOCI_STORAGE_MODE`: `memory` (default, lost on restart) | `persistent` (to `FLOCI_STORAGE_PERSISTENT_PATH`, image `/app/data`; docs disagree on flush timing) | `hybrid` (async flush every 5 s) | `wal` (Azure per-service, e.g. `FLOCI_AZ_STORAGE_SERVICES_BLOB_MODE=wal`).
- CLI `--persist DIR`; drop it for ephemeral CI. `floci <tree> reset --yes` wipes live (not floci-az). `docker compose down -v` deletes the volume.
- Don't rely on `floci snapshot` (skill: every subcommand exits 1). A recreated floci-az container gets a new TLS cert: rerun `floci az setup`.

## Pre-flight checklist before trusting a local result

1. **P0** Real config isolated: `AWS_PROFILE`, `AWS_SESSION_TOKEN`, `GOOGLE_APPLICATION_CREDENTIALS` unset; separate `CLOUDSDK_CONFIG`; `floci az setup` done.
2. **P0** Endpoint asserted local (`localhost`, `127.0.0.1`, `localhost.floci.io`, or a Compose service name) before any mutating command.
3. **P0** Port published on loopback (`127.0.0.1:4566:4566`); unsafe exposure off.
4. **P1** Every service used is tier 1/2, not a stub; Docker socket mounted if tier 1 is needed.
5. **P1** Enforcement modes on and banner confirmed when the claim is about permissions; uncovered services listed.
6. **P1** Apply/destroy round-trips and re-plan shows zero drift.
7. **P2** Image tag pinned; per-job port/profile/namespace; sandbox-account rerun scheduled before promotion.

## Recipe

### AWS CLI smoke (with guardrails)

```sh
export AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null   # [inference]
unset AWS_PROFILE AWS_SESSION_TOKEN GOOGLE_APPLICATION_CREDENTIALS
export CLOUDSDK_CONFIG="$HOME/.floci/gcp/gcloud"
floci aws start --detach --persist ./.floci-aws
floci aws wait --timeout 90s
eval "$(floci aws env -o text)"
echo "$AWS_ENDPOINT_URL" | grep -Eq 'localhost|127\.0\.0\.1' || { echo "NOT LOCAL"; exit 1; }
aws sts get-caller-identity          # expect 000000000000 [inference]
aws s3 mb s3://smoke && aws s3 ls
```

### Terraform / OpenTofu (AWS)
```hcl
# floci_override.tf: keep out of prod code (terraform.md)
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
  endpoints {
    s3  = "http://localhost:4566"
    sts = "http://localhost:4566"   # one line per service used
  }
}
```
```sh
terraform init -backend=false        # never the prod backend
terraform validate && terraform plan -out tf.plan
terraform apply -auto-approve tf.plan
terraform plan -detailed-exitcode    # 0 = no drift, 2 = drift
terraform destroy -auto-approve      # swap terraform -> tofu for OpenTofu
```

- S3 backend: prefer `endpoints = { s3 = ... }` with `use_lockfile = true`; `dynamodb_endpoint`/DynamoDB locking are deprecated ([HashiCorp S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)) [inference].
- Least privilege: restart with `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true`, create a user holding only the deploy role's policy, export its keys, rerun plan/apply; expect `AccessDenied` where too narrow. A pass is evidence, not proof.

```sh
# CDK
npm i -D aws-cdk aws-cdk-local
export LOCALSTACK_HOSTNAME=localhost EDGE_PORT=4566 AWS_ENDPOINT_URL_S3="$AWS_ENDPOINT_URL"
npx cdklocal bootstrap --force
npx cdklocal deploy --require-approval never
npx cdklocal destroy --force
floci aws reset --yes; floci aws stop --remove
```

### Azure

```sh
floci az start --detach --persist ./.floci-az
floci az wait --timeout 90s
floci az setup && eval "$(floci az env -o text)"
az cloud show --query name -o tsv     # MUST be the Floci cloud, not AzureCloud
az group create -n rg-smoke -l westeurope
az deployment group create -g rg-smoke --template-file main.bicep
curl -sf http://localhost:4577/_floci/tls-cert -o floci-az.crt && export SSL_CERT_FILE="$PWD/floci-az.crt"
```
```hcl
# Terraform azurerm (floci.io/floci-az/terraform)
provider "azurerm" {
  features {}
  use_cli         = false
  environment     = "stack"
  metadata_host   = "localhost:4577"
  subscription_id = "00000000-0000-0000-0000-000000000001"
  tenant_id       = "00000000-0000-0000-0000-000000000002"
  client_id       = "11111111-1111-1111-1111-111111111111"
  client_secret   = "floci-az-dev-secret"
}
```

### GCP

```sh
floci gcp start --detach --persist ./.floci-gcp && floci gcp wait --timeout 90s
eval "$(floci gcp env -o text)"
export FIREBASE_AUTH_EMULATOR_HOST=localhost:4588   # not exported by env
E=http://localhost:4588
export CLOUDSDK_CORE_PROJECT=floci-local CLOUDSDK_AUTH_ACCESS_TOKEN=fake CLOUDSDK_CORE_DISABLE_PROMPTS=1
export CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE="$E/storage/v1/" CLOUDSDK_API_ENDPOINT_OVERRIDES_CONTAINER="$E/container/"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER="$E/" CLOUDSDK_API_ENDPOINT_OVERRIDES_CLOUDKMS="$E/" CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM="$E/"
gcloud storage buckets create gs://smoke --log-http 2>&1 | grep -q 'localhost:4588' || { echo "LEAK"; exit 1; }
```

Terraform `google`: `GOOGLE_OAUTH_ACCESS_TOKEN=fake` plus `*_custom_endpoint` per service (e.g. `storage_custom_endpoint = "${endpoint}/storage/v1/"`) from [provider.tf](https://github.com/floci-io/floci-gcp/blob/main/compatibility-tests/compat-terraform/provider.tf). Firestore/Datastore are gRPC-only and unreachable via Terraform; test with SDKs. Reset: `floci gcp reset --yes`.

### Testcontainers

- Java `FlociContainer` (2.x artifact `io.floci:testcontainers-floci-aws` + `-bom`; READMEs disagree, trust the [module README](https://github.com/floci-io/testcontainers-floci)); Azure `FlociAzContainer` with `withTlsConfig(c -> c.enabled(true))`; Node `@floci/testcontainers`, Python `testcontainers-floci`, .NET `Testcontainers.Floci`; GCP `GenericContainer("floci/floci-gcp:latest")` + `Wait.forHttp("/health")`.

### GitHub Actions

Install into `$HOME/.local/bin` (the script calls `sudo` otherwise) (Floci CLI skill, CI reference: [floci-cli skills](https://github.com/floci-io/floci-cli/tree/main/skills/floci)):
```yaml
- name: Install floci
  run: |
    mkdir -p "$HOME/.local/bin"
    curl -fsSL https://floci.io/install.sh | FLOCI_INSTALL_DIR="$HOME/.local/bin" sh
    echo "$HOME/.local/bin" >> "$GITHUB_PATH"
- name: Start emulator
  run: |
    floci aws start --detach
    floci aws wait --timeout 90s
    floci aws env -o json | jq -r 'to_entries[] | "\(.key)=\(.value)"' >> "$GITHUB_ENV"
- run: pytest
```

Service-container alternative (in-process services only; Docker-backed ones need the socket): `services.floci.image: floci/floci:2.4.0`, `ports: ["4566:4566"]`, env `AWS_ENDPOINT_URL=http://localhost:4566`, `test`/`test`, `us-east-1`. Parallel jobs: own port, profile and `--namespace "ci-${GITHUB_RUN_ID}-${GITHUB_JOB}"`.

## Leak-to-real-cloud hazards

| Symptom | Cause | Fix / check |
|---|---|---|
| `gcloud` creates real resources | `gcloud` ignores `*_EMULATOR_HOST` | Set `CLOUDSDK_API_ENDPOINT_OVERRIDES_*`; verify `--log-http` shows `localhost:4588` (only `dl.google.com` update check leaves) |
| `az group create` hits Azure | `floci az setup` not run | Run setup; `az cloud show --query name` must not be `AzureCloud` |
| AWS call goes to real account | `--profile <real>` overrides endpoint, or SDK skips `AWS_ENDPOINT_URL` for SQS | Never pass real profiles; null config files; `aws sts get-caller-identity` |
| `azurerm_key_vault` hangs | Polls `https://<name>.vault.azure.net:443` | Hosts entry/Docker alias to floci-az and forward 443 |
| `floci az wait --service X` times out | floci-az lacks the services endpoint | Use plain `floci az wait` |
| Returned URLs unreachable from app container | Hostname is localhost | Set `FLOCI_HOSTNAME` |

`floci <tree> doctor -o json` returns `{name,status,message,fix}`; do not apply `fix` blindly. Exit codes: 0 ok, 1 failed/"no", 2 bad command line.

## Emulator comparison

| | Floci | LocalStack | moto | Azurite | Google emulators | Cosmos emulator |
|---|---|---|---|---|---|---|
| Clouds | AWS, Azure, GCP, OCI | AWS | AWS | Azure Storage | GCP, one per service | Cosmos |
| Cost | MIT, free | Auth token since Mar 2026; free tier non-commercial; community repo archived ([blog](https://blog.localstack.cloud/the-road-ahead-for-localstack/)) | Apache-2.0 | MIT | Free (gcloud) | Proprietary |
| Shape | One container/port per cloud + real Docker sidecars | One container, 4566 | In-process decorators or `moto_server` :5000 | Blob 10000, Queue 10001, Table 10002 | Pub/Sub 8085, Firestore 8080, Bigtable 8086, Spanner 9010/9020 | Self-signed certs must be trusted |
| Auth/IAM | Off by default; opt-in partial | Paid enforcement [unverified] | None by default [unverified] | Dev account key | Spanner: no TLS/auth/IAM | n/a |
| Best for | Multi-cloud integration, IaC loops | Teams on Pro features | Fast Python unit tests | Storage-only Azure | Spanner/Bigtable fidelity; `gcloud pubsub` unsupported on Pub/Sub emulator | Stored procs, change feed, RU/s |

LocalStack to Floci: swap image to `floci/floci:latest` (or `-compat`), move data mount `/var/lib/localstack` → `/app/data`. LocalStack env vars are auto-translated (`PERSISTENCE=1` → `FLOCI_STORAGE_MODE=persistent`, etc.); `SERVICES` is ignored ([migration guide](https://github.com/floci-io/floci/blob/main/docs/getting-started/migrate-from-localstack.md)).

## Known gaps

- AWS stubs: Bedrock Runtime, Textract, Transcribe, Signer, FIS, QuickSight. Azure: no Cosmos RU/s, global distribution or exact consistency; APIM lacks full policy language and JWT validation; SharedKey unvalidated in `dev` (Blob SAS is); no `floci az reset`.
- GCP: no Spanner or Bigtable; Cloud Functions control plane only; Compute Engine has no guest execution or traffic; Cloud Tasks tracked, not dispatched.
- OCI: no identity domains, dynamic groups, tag namespaces, object versioning, lifecycle, S3 Compatibility API, secret rotation.
- Doc contradictions: `persistent` flush timing, snapshots, `floci start --services`, Testcontainers names. Project is under a year old with two main maintainers (bus factor [inference]); vendor speed claims unreproduced.

## Do / Avoid

**Do**
- Start, wait, wire as three explicit steps; re-`eval` env in every fresh shell; assert the endpoint is local before every mutation.
- Pin image tags in CI; publish ports on `127.0.0.1`; separate namespace/port/profile per parallel instance.
- Mount the Docker socket only for tier-1 services (else `*_MOCK=true`); check a service's tier before coding against it.
- Turn on enforcement for IAM/policy claims and report uncovered services; rerun in a real sandbox with OIDC creds before promotion.

**Avoid**
- `gcloud` with only `*_EMULATOR_HOST`; `az` ARM commands without `floci az setup`; `--profile <real>`; `-q` on `floci env`.
- Curl `healthcheck:` on Floci images; `floci start/restart/stop --remove` against Compose-managed containers.
- Treating stubs as output validation or a permissive green run as least-privilege proof.
- `floci snapshot`; the `-compat` OCI key near real OCI; `FLOCI_SECURITY_ALLOW_UNSAFE_NETWORK_EXPOSURE=true` on shared networks.

Related: `devsecops-pipeline.md`, `aws.md`, `azure.md`, `gcp.md`.

---
name: cloud-devsecops
description: "Docker, Compose, container images and runtimes, Kubernetes operations and ecosystem tooling; security and DevSecOps rules for AWS, Azure and Google Cloud, IAM, policy, pipelines, supply chain and IaC. Use when building or debugging containers, operating workloads, choosing container tools, or changing cloud access and deployment infrastructure."
metadata:
  as-of: "2026-11-13"
---

# Cloud security and DevSecOps reference

Condensed, agent-facing rules distilled on 2026-11-11 from the cited reports in `TimothyVang/cloud-devsecops` (private): https://github.com/TimothyVang/cloud-devsecops. Each file links its full report and keeps the primary-source links for the claims that matter most. `[unverified]` and `[inference]` marks carry over from the reports. Versions, prices, and dates go stale; recheck anything you act on.
Docker/container and Kubernetes references were checked against public primary documentation on 2026-11-13. Other references retain their own check dates.

| File | Read when |
|---|---|
| `references/aws.md` | AWS accounts and Organizations, SCP/RCP/declarative policies, IAM, detection (CloudTrail, GuardDuty, Security Hub, Config), KMS and S3, network controls, CI access to AWS, IaC scanning, AWS security cost |
| `references/azure.md` | Azure management groups and landing zones, Entra ID and workload identity federation, RBAC, Azure Policy, Defender for Cloud, Key Vault, Private Endpoints and DNS, logging, CI access to Azure, AKS |
| `references/gcp.md` | Google Cloud org and projects, IAM and service accounts, org policy constraints, VPC Service Controls, audit logs and SCC, Binary Authorization and SLSA, Workload Identity Federation, GKE |
| `references/devsecops-pipeline.md` | Pipeline security stages and gates, supply chain (SBOM, signing, provenance), scanners, policy as code, container and Kubernetes hardening, GitHub Actions hardening, standards map |
| `references/containers.md` | Docker Engine/Desktop, Compose, BuildKit/buildx, OCI runtimes, Podman, Testcontainers, devcontainers and bounded local container workflows |
| `references/kubernetes.md` | Kubernetes workloads, kubectl context/namespace, probes, Services, storage, Helm/Kustomize, local clusters, GitOps and bounded operational workflows |
| `references/local-emulators.md` | Testing cloud or IaC code without a real account: Floci (AWS, Azure, GCP), LocalStack, moto, Azurite, Google emulators; leak-to-real-cloud checks |
| `references/devops-tools.md` | Choosing terminal, container, Kubernetes, Terraform, observability, secrets, or code-review tooling (one creator's verdicts, DevOps Toolbox) |

Networking fundamentals for AWS (VPC, routing, gateways, flow-log debugging) stay in `skill://domain-rules/references/aws-networking.md`. Deepmodebot's principles, gates, and playbooks win any conflict.

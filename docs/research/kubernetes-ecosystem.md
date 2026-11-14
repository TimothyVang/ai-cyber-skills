# Kubernetes ecosystem: routing and operational evidence

Research date: **2026-11-13**. Scope: official Kubernetes and project-owned documentation for tool selection and safe agent routing. This is a decision reference, not a deployment prescription. No cluster calls, installations, credentials changes, infrastructure mutations or runtime tests were performed. No claim of the latest supported release is made.

Operational single source of truth: [cloud-devsecops Kubernetes reference](../../plugins/deepmodebot/skills/cloud-devsecops/references/kubernetes.md). Existing [DevSecOps pipeline security guidance](../../plugins/deepmodebot/skills/cloud-devsecops/references/devsecops-pipeline.md) owns hardening and supply-chain checklists; this research does not copy its version or release claims.

## Findings and selection decisions

Vendor facts in the middle column come from the cited project. The last column contains **deepmodebot recommendations**, not vendor guarantees or measured comparisons.

| Boundary | Primary-source fact | Selection recommendation |
|---|---|---|
| Kubernetes vs container tooling | Kubernetes stores desired state and continuously reconciles observed state; workload controllers manage Pods. ([objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/), [workloads](https://kubernetes.io/docs/concepts/workloads/)) | Route cluster scheduling, reconcilers, service discovery and storage to Kubernetes. Keep image/build or ordinary local-process failures in the container/application route unless cluster evidence matters. |
| Context and namespace | A kubeconfig context binds cluster, namespace and user; namespace scoping does not apply to Nodes, PVs or StorageClasses. ([contexts](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/), [namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)) | Every cluster goal must name context, namespace and environment. Resolve identity before reads; approval for namespaced work does not authorize cluster-wide inspection or writes. |
| kind | Runs local Kubernetes with container nodes; originally built for Kubernetes testing and also supports local development/CI. ([kind](https://kind.sigs.k8s.io/)) | Default candidate for an explicitly requested disposable Kubernetes CI/reproduction environment, not permission to create it. |
| k3d | Wraps K3s in Docker and supports single/multiple nodes for local development. ([k3d](https://k3d.io/stable/)) | Prefer when K3s is the intentional target or its distribution differences are acceptable; do not call it identical to a managed production cluster. |
| minikube | Local Kubernetes on macOS, Linux and Windows, with addons and development helpers such as tunnel/service access. ([project README](https://raw.githubusercontent.com/kubernetes/minikube/master/README.md)) | Candidate for interactive development needing those helpers. Host/driver/network details must be checked for the actual machine; this research did not benchmark local cluster tools. |
| Helm | Installing a chart creates a release; values customize it. Local template rendering fakes cluster lookups and performs no server-side API-validity testing. ([using Helm](https://helm.sh/docs/intro/using_helm/), [template](https://helm.sh/docs/helm/helm_template/)) | Use existing chart/release workflows for distribution. Inspect exact values and rendered privileges; chart success is not application health. |
| Kustomize | Composes resources and patches, with reusable bases/overlays; integrated into kubectl. ([Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)) | Prefer for direct YAML plus environment variation when a chart package is not required. Avoid redundant templating layers. |
| Argo CD | Declarative GitOps delivery compares live/desired application state, exposes sync differences, health analysis and a UI. ([Argo CD](https://argo-cd.readthedocs.io/en/stable/)) | Candidate when application-centric visualization/operations is the requirement. Preserve current ownership and separate Git sync, resource health and business checks. |
| Flux | Its documented workflow bootstraps controllers, tracks Git sources and applies Kustomizations; direct edits can be reverted to Git state. ([Flux guide](https://fluxcd.io/flux/get-started/)) | Candidate for controller/resource-oriented GitOps. Bootstrap has repository and cluster side effects; research/diagnosis must not execute it. |
| Ingress/Gateway API | Ingress is frozen and requires a controller; Kubernetes recommends Gateway. Gateway's CRDs split class, listener/gateway and route roles, with controlled route attachment and implementation-dependent optional features. ([Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/), [Gateway overview](https://gateway-api.sigs.k8s.io/docs/concepts/api-overview/)) | Evaluate Gateway for new routing requirements with implementation/conformance evidence. Preserve existing supported Ingress rather than silently migrating. DNS/controller/backend/TLS must all be proven on the intended path. |
| Metrics Server | Resource-metric source for autoscaling and `kubectl top`; explicitly not a full monitoring source. ([Metrics Server](https://kubernetes-sigs.github.io/metrics-server/)) | Use for CPU/memory/autoscaling investigation when already present. Missing historical latency evidence is not solved by `top`. |
| Prometheus | Stores metric time series, uses PromQL, scrapes targets and evaluates alerting/recording rules. Kubernetes components expose Prometheus-format metrics. ([Prometheus](https://prometheus.io/docs/introduction/overview/), [Kubernetes metrics](https://kubernetes.io/docs/concepts/cluster-administration/system-metrics/)) | Use existing dashboards/queries for sustained latency, errors and capacity. Do not add broad `/metrics` permissions just to collect evidence. |
| OpenTelemetry | Collector receives/processes/exports telemetry; Kubernetes Operator manages collectors and workload auto-instrumentation. Collector component maturity varies. ([Collector](https://opentelemetry.io/docs/collector/), [Kubernetes integration](https://opentelemetry.io/docs/platforms/kubernetes/)) | Use when cross-service traces/metrics/logs or vendor-neutral transport are needed. Choose actual receivers/exporters/backend and data-redaction policy; an installed collector alone proves nothing about delivery. |
| Kyverno/Gatekeeper | Kyverno supports policy validation/mutation/generation/image verification and CLI/runtime workflows. Gatekeeper supplies OPA-backed admission plus audit of existing resources. ([Kyverno](https://kyverno.io/docs/introduction/), [Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/)) | Extend the existing policy system only for unmet controls. Match installed policy APIs and organizational expertise; separate audit/reporting from enforcement, and treat admission changes as production-risk changes. |

## Facts that constrain troubleshooting

- **Controller health is not application health.** Probes have different meanings: startup gates initialization; readiness controls traffic eligibility; liveness can restart. A rollout can converge with a shallow readiness endpoint while the original business operation still fails. Preserve the original client path/data contract and measure both outcomes. This conclusion is a recommendation derived from [probe semantics](https://kubernetes.io/docs/concepts/workloads/pods/probes/) and [revision-aware rollout watching](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/kubectl_rollout_status/).
- **Bound retries at both layers.** The agent needs fixed investigation/change/time budgets; the workload has separate Job `backoffLimit` and `activeDeadlineSeconds`. CronJob schedules are approximate and jobs should be idempotent. Repeatedly recreating failed work is not a diagnostic strategy. ([Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/), [CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/))
- **Inspect the right failure domain.** Requests affect scheduling; CPU limits can throttle; memory limits can cause OOM termination. Service selectors/EndpointSlices and caller-namespace DNS are independent from healthy application responses. ([resources](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/), [Service](https://kubernetes.io/docs/concepts/services-networking/service/), [DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/))
- **Configuration and persistence need application evidence.** ConfigMap environment consumers need restart to update and `subPath` consumers do not receive updates. PVC/PV binding and reclaim policy affect data lifetime; `Delete` can remove backing storage. Recommendations: establish reload behavior and recovery requirements before rollout or storage repair; a mounted file or bound PVC is not proof of successful reload/durability. ([ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/), [persistent volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/))
- **Security objects are not security proof.** RBAC allows additively, Pod Security warn/audit do not block, and Pod enforcement occurs after a controller creates Pods rather than at Deployment-template acceptance.
  Secrets are not encrypted at rest by Kubernetes default; permissions to create Pods can expose namespace Secrets.
  NetworkPolicy needs enforcement by a network plugin, has additive allows and L3/L4 scope, and has host/existing-connection/timing limitations.
  Recommendation: require exact privilege/policy scope and authorized positive/negative runtime checks, not blanket access or policy deletion.
  ([RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/), [Pod Security](https://kubernetes.io/docs/concepts/security/pod-security-admission/), [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/), [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/))

## Goal and self-prompt integration contract

**Recommendation:** the automatic router should load the Kubernetes reference for explicit cluster objects/commands or evidence of a cluster-layer failure, then retain the original application/bug oracle. Its self-prompt should answer these questions before choosing tools:

1. Which exact context, namespace, object, environment and desired revision are in scope, and which reads/writes have been authorized?
2. Is this render validation, API acceptance, controller convergence, network enforcement, or application runtime proof? Which is actually requested?
3. What immutable original request/test establishes success? What baseline, data effects and observation window apply?
4. Who owns desired state: manifest, chart/release, Kustomize overlay or GitOps controller? Would a live patch be reverted?
5. What one hypothesis does the next bounded read test? What time/round/mutation cap terminates the loop?
6. Does the next action change production, credentials, security controls, persistent data or publication? If yes, is exact approval present?

Suggested bounded goals (recommendations, not executed tests):

| Goal | Evidence and stopping rule |
|---|---|
| Diagnose a Pending/CrashLooping Pod | Start with its owner/status/events and selected container logs; explain one supported cause within three evidence rounds/ten minutes. Zero mutations until approved; stop at cap or missing permission. |
| Validate a chart/overlay | Render chosen values/overlay and inspect names, namespace, images, resources, config references and privileges. Report only artifact evidence; server dry-run is a separately authorized target-cluster action. |
| Observe an approved rollout | Pin context/namespace/revision and finite timeout; require both convergence and original application oracle during the agreed window. A competing revision, error regression or exceeded cap stops the operation. Rollback requires its own preauthorization. |
| Diagnose a service route | Follow the original client's DNS/namespace, Service/EndpointSlices and controller route. No substitute loopback/port-forward success accepted as external-route proof. Active requests or debug Pods require explicit authorization. |
| Assess network/policy changes | Establish actual plugin/admission mode and intended allow/deny cases. Manifest acceptance is insufficient; runtime tests remain `not observed` if access/approval is absent. |

These goals intentionally do not grant permission to deploy, create clusters, sync GitOps applications, add CRDs, bootstrap controllers, or change kubeconfig defaults.

## Validation is a ladder, not a synonym for success

- **Template/local rendering** establishes output generation only. Helm documents fake local cluster lookups and absent server-side validation. ([Helm template](https://helm.sh/docs/helm/helm_template/))
- **Client dry-run** describes the would-be object without sending it for persistence; avoid promising an entirely offline process for every client validation path. ([kubectl apply](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/))
- **Server dry-run** evaluates admission/defaulting/validation/merge without persistence and requires the same authorization as the real operation. It is neither ordinary read-only access nor proof of scheduling, image pulls, controller action, storage, networking or application behavior. ([API dry-run](https://kubernetes.io/docs/reference/using-api/api-concepts/#dry-run))
- **Real runtime evidence** is environment-specific. A local-cluster pass is not managed-cloud IAM/CNI/CSI/load-balancer equivalence. Record separate outcomes for rendered manifests, API validation, rollout and the original application oracle. This reporting distinction is a recommendation.

## Source manifest

All successful sources below were read on **2026-11-13**. Dates are retrieval dates, not guarantees that every page is contemporaneous with an installed cluster. Long pages were read in relevant sections, not claimed exhaustively audited. Moving `main`, `master`, `stable` and unversioned docs must be resolved to the deployed version before implementation.

| Actual URL read | Evidence used |
|---|---|
| https://kubernetes.io/docs/concepts/overview/working-with-objects/ | Desired/observed state, API objects |
| https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/ | Context precedence, kubeconfig trust |
| https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/ | Namespace scope and cluster-wide objects |
| https://kubernetes.io/docs/concepts/workloads/ | Controller selection |
| https://kubernetes.io/docs/concepts/workloads/controllers/job/ | Retry/deadline bounds |
| https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ | Scheduling/concurrency/idempotency |
| https://kubernetes.io/docs/concepts/workloads/pods/probes/ | Probe roles; reached through the older configuration/probes URL |
| https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ | Requests, limits, throttling/OOM |
| https://kubernetes.io/docs/concepts/services-networking/service/ | Selectors, EndpointSlices |
| https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/ | Namespace-relative DNS and cluster domain |
| https://kubernetes.io/docs/concepts/services-networking/ingress/ | Frozen API, controller requirement |
| https://gateway-api.sigs.k8s.io/docs/concepts/api-overview/ | Gateway roles, attachment, implementation support |
| https://raw.githubusercontent.com/kubernetes-sigs/gateway-api/main/README.md | Project ownership, CRDs and conformance pointers; version claims not adopted |
| https://kubernetes.io/docs/concepts/configuration/configmap/ | Configuration secrecy and propagation limits |
| https://kubernetes.io/docs/concepts/configuration/secret/ | Storage defaults and privilege implications |
| https://kubernetes.io/docs/concepts/storage/persistent-volumes/ | PVC/PV binding and reclaim policy |
| https://kubernetes.io/docs/reference/access-authn-authz/rbac/ | Additive permissions and binding scope |
| https://kubernetes.io/docs/concepts/security/pod-security-admission/ | Modes, template vs Pod enforcement, exemptions |
| https://kubernetes.io/docs/concepts/services-networking/network-policies/ | Enforcing plugin, additive policy, protocol/host/runtime limits |
| https://kubernetes.io/docs/reference/using-api/api-concepts/ | Server dry-run semantics and authorization |
| https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/ | Client/server dry-run flags |
| https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/kubectl_rollout_status/ | Revision pinning and finite timeout |
| https://kind.sigs.k8s.io/ | Local container-node clusters and CI/testing use |
| https://k3d.io/stable/ | K3s-in-Docker role; canonical page reported `https://k3d.io/v5.9.0/` |
| https://raw.githubusercontent.com/kubernetes/minikube/master/README.md | Cross-platform development goals and addons |
| https://helm.sh/docs/intro/using_helm/ | Charts/releases/values |
| https://helm.sh/docs/helm/helm_template/ | Local rendering limitations |
| https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/ | Composition, patches, bases/overlays |
| https://argo-cd.readthedocs.io/en/stable/ | GitOps application sync/diff/health model |
| https://fluxcd.io/flux/get-started/ | Reconciliation, bootstrap side effects and drift correction |
| https://kubernetes.io/docs/concepts/cluster-administration/system-metrics/ | Component metrics and access control |
| https://kubernetes-sigs.github.io/metrics-server/ | Autoscaling/top scope and monitoring limitations |
| https://prometheus.io/docs/introduction/overview/ | Time series, queries and alerting |
| https://opentelemetry.io/docs/platforms/kubernetes/ | Collector/Operator integration |
| https://opentelemetry.io/docs/collector/ | Receive/process/export; reader used `https://opentelemetry.io/docs/collector/index.md` alternate |
| https://kyverno.io/docs/introduction/ | Policy capabilities, CLI/admission/runtime |
| https://open-policy-agent.github.io/gatekeeper/website/docs/ | OPA admission and audit |

### Retrieval limitations and unresolved compatibility

- `https://gateway-api.sigs.k8s.io/` returned a redirect page; `/docs/` and `/docs/introduction/` returned only an alternate-feed title. The substantive API overview and project README above supplied Gateway evidence. An attempted `https://raw.githubusercontent.com/kubernetes-sigs/gateway-api/main/site-src/index.md` returned HTTP 404 and supports no claim.
- `https://minikube.sigs.k8s.io/docs/` and `/docs/start/` returned only feed titles; the official repository README supplied substantive evidence. `https://fluxcd.io/flux/` likewise returned a feed title; `/flux/get-started/` supplied evidence. The extraction issue was reported to the tool system.
- The probe request `https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/` redirected to the probes URL in the manifest.
- Unversioned Kubernetes pages contained release-specific feature text, and Gateway README/API-overview maturity statements differed for some route kinds. No latest-release or blanket support claim was retained. Confirm installed Kubernetes/CRD/controller versions and implementation conformance before changing features.
- No target cluster, CNI, CSI, Gateway controller, chart dependency set, policy version or telemetry backend was inspected. Therefore platform compatibility, runtime health, real isolation, performance and production readiness remain **unverified**.

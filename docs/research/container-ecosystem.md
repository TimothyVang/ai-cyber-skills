# Container ecosystem: evidence and routing decisions

**Checked:** 2026-11-13. **Method:** read official project/vendor documentation and first-party source; no installations, CLI/container runs, builds, tests, daemon changes, or cluster operations. Commands in the operational reference were checked against documentation only, not executed or validated against an installed version. Live documentation is mutable; this is a dated research note, not a latest-version inventory.

Operational single source of truth: [containers.md](../../plugins/deepmodebot/skills/cloud-devsecops/references/containers.md). Security pipeline policy remains in [devsecops-pipeline.md](../../plugins/deepmodebot/skills/cloud-devsecops/references/devsecops-pipeline.md); that existing file's version/date claims were not revalidated in this research.

## Decision summary

The **vendor facts** below establish what each layer does. The **recommendations** are deepmodebot routing policy, not product guarantees.

| Branch | Vendor evidence | Recommendation |
|---|---|---|
| Docker access | Engine exposes a daemon/API/CLI; Docker CLI client and server can be on different machines ([Engine](https://docs.docker.com/engine/), [version](https://docs.docker.com/reference/cli/docker/version/)) | Inspect context, endpoint, overrides, permissions, server OS, and versions before choosing commands. Prefer the existing CLI over adding MCP |
| Desktop vs Engine | Desktop bundles tools; Linux Desktop has a separate VM, storage, and context; Windows can use Linux or Windows containers ([Desktop](https://docs.docker.com/desktop/), [Linux installation architecture](https://docs.docker.com/desktop/setup/install/linux/)) | Do not assume workstation OS identifies container OS or that Desktop and host Engine share images/data. No automatic engine installation/context switching |
| Compose | The supported modern interface is `docker compose`; v2 uses the Compose Specification rather than the historical versioned file formats. The checked history also describes v5 and its Go SDK ([history](https://docs.docker.com/compose/intro/history/)) | Cover the requested v2 workflow without calling it the latest version. Fix file list/project/context explicitly; no migration merely to replace a top-level version number |
| Image builds | Buildx is a client, BuildKit executes builds; named stages, cache mounts, and secret mounts have distinct purposes ([overview](https://docs.docker.com/build/concepts/overview/), [multi-stage](https://docs.docker.com/build/building/multi-stage/), [cache](https://docs.docker.com/build/cache/optimize/), [secrets](https://docs.docker.com/build/building/secrets/)) | Inspect the selected builder separately from Docker context. Treat build execution, remote cache writes, secret access, and registry push as separate permissions |
| Runtime diagnosis | Compose service discovery uses names/container ports; volumes outlive containers; startup is not readiness; default containers lack resource caps ([networking](https://docs.docker.com/compose/how-tos/networking/), [volumes](https://docs.docker.com/engine/storage/volumes/), [readiness](https://docs.docker.com/compose/how-tos/startup-order/), [constraints](https://docs.docker.com/engine/containers/resource_constraints/)) | Diagnose network/mount/health/limits directly. Repeated recreation, broader privileges, and global prune are not diagnosis |
| Standards/runtime | OCI defines image/runtime/distribution specifications; containerd manages container lifecycle; runc runs OCI containers on Linux ([OCI](https://opencontainers.org/about/overview/), [containerd](https://containerd.io/), [runc](https://github.com/opencontainers/runc)) | Route standards/runtime-internal questions here, not to a generic orchestration or Dockerfile answer |
| Alternative engine | Podman is daemonless and Linux-native, supports non-privileged operation, and offers remote clients/API service ([Podman](https://docs.podman.io/en/latest/)) | Respect the repository's engine choice. CLI similarity is not proof that every Docker API/Testcontainers workflow works unchanged |
| Test dependencies | Testcontainers creates disposable dependencies. Java's binding documents Docker-API compatibility, runtime discovery, and caveats for alternative runtimes ([project](https://testcontainers.com/), [Java requirements](https://java.testcontainers.org/supported_docker_environment/)) | Use the existing language binding/test runner. Do not generalize Java-specific discovery or cleanup options to other bindings; inspect actual endpoint ownership |
| Developer workspace | Development Containers describes environment metadata; `initializeCommand` executes on the host and other lifecycle hooks execute during container setup/start/attach ([spec site](https://containers.dev/), [metadata source](https://raw.githubusercontent.com/devcontainers/spec/main/docs/specs/devcontainerjson-reference.md)) | Inspect hooks, features, mounts, and user/privilege configuration before opening. A devcontainer is not automatically safe for hostile repositories |

## Authority and lifecycle conclusions

- **Vendor fact:** trusted users only should control the Docker daemon; arbitrary host mounts can permit host modification, and capabilities/mounts/kernel vulnerabilities affect isolation ([Docker security](https://docs.docker.com/engine/security/)). **Recommendation:** treat Docker socket access as daemon authority, even if mounted read-only. A container is not a complete hostile-code sandbox. MCP transport does not reduce the permissions of the daemon connection behind it.
- **Vendor fact:** context/environment/CLI flags choose the daemon; Compose `-f` and `-p` determine the application scope ([contexts](https://docs.docker.com/engine/manage-resources/contexts/), [Compose CLI](https://docs.docker.com/reference/cli/docker/compose/)). **Recommendation:** bind these once per goal and preserve them through diagnosis, execution, and cleanup; reject authority changes mid-loop.
- **Vendor fact:** `up --wait` waits for running/healthy, while `--wait-timeout` bounds that wait. `down --timeout` is a shutdown timeout. Named and anonymous volume deletion requires `down --volumes`; anonymous volumes are not automatically reattached later ([up](https://docs.docker.com/reference/cli/docker/compose/up/), [down](https://docs.docker.com/reference/cli/docker/compose/down/)). **Recommendation:** an outer execution deadline, explicit application acceptance, owned-resource cleanup, and retained-volume report are necessary. Keep volume data; never use global prune as automatic cleanup.
- **Recommendation:** permission denied is a stop-and-diagnose condition, not a retry policy. At most retry an observed transient failure within the original attempt/time bounds; never use retries to widen access, select another daemon, or disable security controls.

## Routing and self-prompt acceptance cases

These are recommended integration cases for routing/evaluations; no evaluator was run here.

| Input | Expected route and evidence | Reject |
|---|---|---|
| "Docker works in my terminal but my tests cannot connect" | Container reference, existing Testcontainers binding docs, daemon endpoint and SDK discovery | Assuming all SDKs inherit Docker CLI context; installing an MCP server |
| "Compose db is running but api fails on startup" | Container reference: healthcheck semantics and scoped logs | Endless `restart`; treating process-running as ready |
| "Build is slow; private package token appears in layers" | BuildKit/buildx, context/cache and secret mount branch; pipeline reference for scanning | `ARG` secrets; blanket cache deletion; secrets passed to untrusted Dockerfile |
| "Can this agent safely run hostile code in Docker with the socket?" | Authority boundary and isolation limits | Calling ordinary containers or a read-only socket mount a security sandbox |
| "Clean my project, keep the database" | Fix context/project, identify owned resources, preserve volume identities | `down -v`, global prune, or removal of shared resources |
| "Use my existing Podman setup" | Podman engine plus workflow-specific compatibility | Silently aliasing Docker or installing Desktop |
| "Open the repo's devcontainer" | Inspect initialization/lifecycle hooks, features, host mounts, users | Treating host initialization as container-confined |
| "Run until it works" | Require fixed context/project/acceptance, wall timeout, resource/attempt/output caps, and scoped cleanup | Unbounded loop or retry after access denial |

The operational reference supplies read-only diagnosis, authorized disposable integration, and build-planning goal/self-prompt examples. They distinguish readiness timeout from whole-workflow timeout, require explicit resource bounds before starting, and preserve data on both success and failure. The examples do not authorize any execution in this research task.

## Source manifest

All sources below were actually read on **2026-11-13**. Docker pages generally returned official `.md` alternates; links retain their canonical readable URLs. "Relevant sections" means only the visible relevant content was used, not a claim that every line of a long page was inspected.

| Source read | Used for / coverage |
|---|---|
| https://docs.docker.com/engine/ | Engine client-server architecture; overview |
| https://docs.docker.com/desktop/ | Desktop components and Windows/Linux container support; overview |
| https://docs.docker.com/desktop/setup/install/linux/ | Separate VM/context/storage, coexistence; full returned page |
| https://docs.docker.com/compose/ | Multi-container application role; overview |
| https://docs.docker.com/compose/install/ | Desktop/plugin/legacy standalone distinction |
| https://docs.docker.com/compose/intro/history/ | v1/v2/v5 and file-format distinction; no inferred latest release |
| https://docs.docker.com/build/ | Build ecosystem overview |
| https://docs.docker.com/build/concepts/overview/ | Buildx/BuildKit responsibility split |
| https://docs.docker.com/build/building/multi-stage/ | Named stages, copying artifacts, target dependencies |
| https://docs.docker.com/build/cache/optimize/ | Layer ordering, context, cache mounts, builder-local caches; relevant sections |
| https://docs.docker.com/build/building/secrets/ | Secret/SSH mounts, build arguments/environment caveat |
| https://docs.docker.com/engine/manage-resources/contexts/ | Endpoint/override selection and inspection |
| https://docs.docker.com/engine/security/ | Daemon authority and container isolation limitations |
| https://docs.docker.com/compose/how-tos/networking/ | Service names, container vs host ports, network scope; relevant sections |
| https://docs.docker.com/engine/storage/volumes/ | Persistence, mount obscuring, named/anonymous volumes; relevant sections |
| https://docs.docker.com/compose/how-tos/startup-order/ | Dependency conditions and healthchecks |
| https://docs.docker.com/engine/containers/resource_constraints/ | Unconstrained defaults, CPU/memory semantics and support |
| https://docs.docker.com/reference/cli/docker/compose/ | Explicit project/files, precedence, `ps -a`, CLI subcommands |
| https://docs.docker.com/reference/cli/docker/compose/config/ | Validation without rendered output; interpolation |
| https://docs.docker.com/reference/cli/docker/compose/logs/ | `--tail` per-container limit and `--no-color` |
| https://docs.docker.com/reference/cli/docker/compose/up/ | Build/pull/recreate effects, wait options |
| https://docs.docker.com/reference/cli/docker/compose/down/ | Default cleanup scope, volume preservation/deletion, shutdown timeout |
| https://docs.docker.com/reference/cli/docker/version/ | Client/server versions and API negotiation |
| https://docs.docker.com/reference/cli/docker/buildx/ls/ | Builder nodes/endpoints/platforms and status timeout |
| https://opencontainers.org/about/overview/ | Three OCI specifications and their responsibilities |
| https://containerd.io/ | Daemon and lifecycle responsibilities; not a version audit |
| https://github.com/opencontainers/runc | Repository README introduction and Linux scope; relevant sections |
| https://docs.podman.io/en/latest/ | Engine, rootless, remote client/service roles; no latest-version inference |
| https://testcontainers.com/ | Test dependency libraries and language bindings; relevant sections |
| https://java.testcontainers.org/supported_docker_environment/ | Java-specific runtime compatibility, discovery, alternative-runtime caveats |
| https://containers.dev/ | Open development-environment specification |
| https://raw.githubusercontent.com/devcontainers/spec/main/docs/specs/devcontainerjson-reference.md | Metadata, privileges, mounts, users, lifecycle execution locations |

Retrieval caveats: `https://docs.docker.com/compose/releases/migrate/` redirected to the Compose overview, so the history page supplied version evidence. `https://containers.dev/implementors/json_reference/` returned only page metadata in the reader, so the official specification repository's raw Markdown supplied the substantive evidence. No conclusions rely on content missing from either response.

## Limitations and refresh triggers

- No local Docker/Podman/Desktop availability, context, daemon access, installed plugin flags, rootless constraints, architecture, or effective resource caps were observed. A documentation-checked command is not an execution result.
- No image pulls/builds, registry access, tests, runtime health assertions, cleanup, or hostile-code isolation experiments were performed. No recommendation establishes a security boundary by testing.
- Runtime compatibility is platform/version/binding-specific. Testcontainers' Java documentation is not evidence for every language implementation. Podman API compatibility must be verified for the requested workflow.
- Live docs may gain flags or change support statements. Recheck installed CLI help and relevant official docs before execution; do not install/upgrade merely because documentation is newer.
- This slice intentionally does not duplicate Kubernetes operations, cloud IAM policy, supply-chain gates, or agent harness configuration. It provides routing facts and bounded execution contracts for the owning references to consume.

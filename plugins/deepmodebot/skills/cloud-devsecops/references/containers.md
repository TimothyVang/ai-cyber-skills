# Docker and container workflows

Read when choosing or operating Docker Engine/Desktop, Compose, BuildKit/buildx, Podman, Testcontainers, or development containers; diagnosing image builds, daemon access, container networking, storage, health, or resource use. Checked **2026-11-13** against primary documentation. Commands below are **documentation-checked, not executed**; installed versions, endpoints, and permissions remain unknown.

This file's routing, bounds, and permission rules are **deepmodebot recommendations**, not vendor guarantees. Security gates, image provenance/signing, vulnerability scanning, and runtime hardening stay in [devsecops-pipeline.md](devsecops-pipeline.md). Source manifest and research limitations: [container-ecosystem.md](https://github.com/TimothyVang/deepmodebot/blob/main/docs/research/container-ecosystem.md).

## Choose the layer, not another tool

| Need | Vendor fact | Recommended route |
|---|---|---|
| Manage images, containers, networks, volumes | [Engine](https://docs.docker.com/engine/) is a daemon/API/CLI system; [Desktop](https://docs.docker.com/desktop/) bundles Engine, CLI, Compose, Build, and desktop integrations | Existing CLI first. Desktop is not required merely because a Dockerfile exists. Identify the actual daemon before operating |
| Local multi-service lifecycle | [Compose](https://docs.docker.com/compose/) models services, networks, and volumes | Use repository Compose files and `docker compose`, not a newly installed MCP server |
| Build images | [Buildx is the client; BuildKit is the execution backend](https://docs.docker.com/build/concepts/overview/) | Inspect builder endpoint/platform; edit Dockerfile/build configuration before changing runtime tooling |
| Explain interoperability/runtime internals | [OCI](https://opencontainers.org/about/overview/) specifies image, runtime, and distribution formats; [containerd](https://containerd.io/) manages host container lifecycle; [runc](https://github.com/opencontainers/runc) runs OCI containers on Linux | Use these for format/runtime diagnosis, not as interchangeable Compose replacements |
| Existing Podman environment | [Podman](https://docs.podman.io/en/latest/) is a daemonless Linux-native engine with rootless support and remote clients | Keep the existing engine; check API/workflow compatibility instead of silently aliasing Docker or installing another engine |
| Real disposable dependencies in tests | [Testcontainers](https://testcontainers.com/) provides throwaway dependencies through language libraries | Use the repository's language binding and test runner; inspect its runtime discovery separately from Docker CLI context |
| Reproducible developer workspace | [Development Containers](https://containers.dev/) is a development-environment specification | Inspect `.devcontainer` configuration, features, mounts, users, and lifecycle commands before opening/rebuilding it |

**Compose v2 does not mean Compose file version 2.** V2 uses `docker compose` and the rolling Compose Specification, ignoring the top-level `version` field. The checked [history page](https://docs.docker.com/compose/intro/history/) also documents v5 with the same CLI behavior and a Go SDK; do not claim v2 is the latest release. Legacy standalone installation is retained for backward compatibility, not the recommended route ([installation](https://docs.docker.com/compose/install/)).

## Preflight: scope and authority before execution

1. Read existing Dockerfile, Compose files/overrides, `.dockerignore`, and relevant repository instructions. Fix the working directory, explicit file list, profiles, env-file selection, project name, service subset, image identity, and intended daemon. Completion: the run cannot accidentally discover a parent-directory Compose file or target another project ([Compose scope/precedence](https://docs.docker.com/reference/cli/docker/compose/)).
2. Inspect contexts with `docker context ls` and `docker context inspect NAME`; inspect relevant `DOCKER_HOST`, `DOCKER_CONTEXT`, and `DOCKER_API_VERSION` overrides without dumping unrelated environment variables or credentials. Then use explicit `docker --context NAME ...`, not persistent `context use`. Completion: approved endpoint and local/remote ownership are known ([contexts](https://docs.docker.com/engine/manage-resources/contexts/), [API negotiation](https://docs.docker.com/reference/cli/docker/version/)).
3. Run bounded read-only probes against that endpoint: `docker --context NAME version`, `docker --context NAME info`, and `docker compose version`. For builds, inspect builder nodes/endpoints with `docker --context NAME buildx ls`; record the chosen builder separately. Listing builders may contact their endpoints, so restrict discovery to approved infrastructure. Completion: client/server distinction, daemon OS/architecture, plugin availability, and resource-support warnings are recorded ([version](https://docs.docker.com/reference/cli/docker/version/), [resource support](https://docs.docker.com/engine/containers/resource_constraints/), [builders](https://docs.docker.com/reference/cli/docker/buildx/ls/)).
4. Classify the requested operation: file review/config validation; read-only daemon inspection; build/pull; runtime mutation; registry push; deletion. A build executes repository code and may contact registries; `up` creates/recreates resources. Do not promote a read-only request into these operations ([BuildKit](https://docs.docker.com/build/concepts/overview/), [up](https://docs.docker.com/reference/cli/docker/compose/up/)). Completion: only authorized effects remain.

Desktop is not synonymous with the host Engine. On Linux, Desktop runs its own VM and `desktop-linux` context with isolated images/containers; a host Engine can coexist. Windows Desktop supports Linux/Windows container selection and WSL 2/Hyper-V paths. Diagnose the selected server, not the workstation OS alone ([Desktop Linux](https://docs.docker.com/desktop/setup/install/linux/), [Desktop](https://docs.docker.com/desktop/)).

**Authority boundary:** controlling a rootful Docker daemon can permit arbitrary host mounts and host filesystem modification.
Giving an agent, MCP server, test helper, or container the Docker socket grants daemon authority, not merely visibility.
A read-only bind mount of a socket is not API authorization.
Prefer minimum privileges and already approved tooling; never fix permission denied by widening socket permissions, enabling privileged mode, or disabling TLS.
Containers are not a complete hostile-code sandbox: kernel vulnerabilities, capabilities, mounts, and daemon access affect isolation ([Docker security](https://docs.docker.com/engine/security/)).
The socket/API consequence and sandbox rule are security recommendations derived from that threat model.

MCP is optional only when an already approved server provides a necessary capability absent from the existing CLI. Inspect its endpoint, credentials, exposed operations, and authorization first; a structured tool response does not reduce daemon privileges. A Docker daemon itself does not imply that any Docker MCP server is installed or authorized.

## Build branch

- Use named multi-stage builds and copy only required artifacts into the runtime stage. `--target` selects an existing stage; BuildKit skips unrelated stages ([multi-stage builds](https://docs.docker.com/build/building/multi-stage/)).
- Put stable dependency inputs before frequently changing source, keep context small with `.dockerignore`, and use package-manager-appropriate cache mounts. Builder caches are separate; external cache export/import is an explicit storage/registry decision, not free global state ([cache guidance](https://docs.docker.com/build/cache/optimize/)). Recommendation: scope external caches by repository/trust boundary and approve remote writes separately.
- Use BuildKit secret/SSH mounts for authorized build credentials, not `ARG`/`ENV` or copied credential files. Secret mounts expose data for the build instruction; they do not stop an untrusted instruction from copying or leaking it ([build secrets](https://docs.docker.com/build/building/secrets/)). Recommendation: review the consuming build command, avoid credential logging, and never supply secrets to untrusted build code.
- Acceptance must name the target platform, runtime artifact, and relevant test/output. Build success alone does not establish runtime compatibility. Keep scan/sign/provenance policy in [devsecops-pipeline.md](devsecops-pipeline.md).

## Runtime branch

| Symptom/design decision | Evidence to inspect and bounded next step |
|---|---|
| Service cannot reach database | Use Compose service DNS name and container port for service-to-service traffic, not a recreated container IP or host-published port. Check shared networks before adding ports; prefer loopback host publishing for local-only access ([networking](https://docs.docker.com/compose/how-tos/networking/)) |
| Data disappeared after recreate | Check mount identity and destination. Named volumes persist beyond container removal; mounting over files obscures them. Anonymous volumes do not automatically reconnect on a later `up` after `down` ([volumes](https://docs.docker.com/engine/storage/volumes/), [down](https://docs.docker.com/reference/cli/docker/compose/down/)). Preserve data and investigate before recreating anything |
| Process running but dependency unavailable | Startup order is not readiness. Use an application-relevant healthcheck with bounded timeout/retries and `depends_on: condition: service_healthy` where appropriate. `up --wait` accepts running OR healthy, so require healthchecks and an application assertion when readiness matters ([startup order](https://docs.docker.com/compose/how-tos/startup-order/), [up](https://docs.docker.com/reference/cli/docker/compose/up/)) |
| OOM or host overload | Containers are unconstrained by default. Set explicit memory/CPU caps appropriate to the workload; inspect daemon support and effective limits. CPU shares are a relative weight, not a hard CPU cap; memory reservation is not a hard memory cap ([constraints](https://docs.docker.com/engine/containers/resource_constraints/)) |
| Permission/API failure | Preserve the error and endpoint; distinguish unavailable daemon, wrong context, denied socket access, registry authentication, and unsupported API. Retry does not change authorization. Stop at the boundary rather than install an engine, switch context, or escalate privileges |
| Testcontainers cannot connect | The Java implementation requires Docker-API compatibility and documents environment-based discovery; alternate runtimes are not all actively tested. Do not assume CLI context selection controls every language binding. Check that binding's docs and cleanup ownership before running tests ([runtime requirements](https://java.testcontainers.org/supported_docker_environment/)) |
| Devcontainer setup is unsafe | `initializeCommand` runs on the host; other lifecycle hooks can execute in the container, with workspace mounts and configured privileges. `remoteUser` does not change every container process. Review hooks/features before execution; an editor workspace is not a hostile-code sandbox ([metadata source](https://raw.githubusercontent.com/devcontainers/spec/main/docs/specs/devcontainerjson-reference.md)) |

## Bounded recipes and self-prompts

These are **recommended future-run templates, not permission to run them now**. Bind names to observed, approved resources before starting; if a literal does not match the environment, revise the run contract rather than creating it. All examples assume a reviewed local `desktop-linux` context, repository cwd, `compose.yaml`, and project `deepmodebot-container-check`. This context is an example for Linux Desktop, not a Windows default. An outer runner must enforce wall time and retain enough time for scoped cleanup: a CLI wait/shutdown flag is not a whole-workflow deadline.

### Read-only diagnosis

Goal/self-prompt: "Explain why `api` is unhealthy in `deepmodebot-container-check` on verified `desktop-linux`. Read only `compose.yaml` and this project's state. Acceptance: report endpoint, failing health condition, and evidence-backed next action without changing resources. Budget: 120 seconds total, 20 seconds per CLI call, at most six CLI calls, no retries after access denial, at most 100 log lines per container. Redact credentials."

After preflight, select only necessary commands:

```sh
docker --context desktop-linux compose -f compose.yaml -p deepmodebot-container-check config --quiet
docker --context desktop-linux compose -f compose.yaml -p deepmodebot-container-check ps -a
docker --context desktop-linux compose -f compose.yaml -p deepmodebot-container-check logs --no-color --tail 100 api
```

`config --quiet` validates without printing the resolved model; ordinary `config` can render interpolated values. `logs --tail` caps lines per container, not total bytes; the runner must additionally cap captured output (for example 64 KiB). Sources: [config](https://docs.docker.com/reference/cli/docker/compose/config/), [Compose](https://docs.docker.com/reference/cli/docker/compose/), [logs](https://docs.docker.com/reference/cli/docker/compose/logs/).

### Authorized disposable integration run

Goal/self-prompt: "Exercise only reviewed `api` and its declared dependencies using project `deepmodebot-container-check`, context `desktop-linux`, and `compose.yaml`. Start only if this project is unused and image digests are already local. Acceptance: configured healthchecks pass and the repository's one named API assertion succeeds. Cap: one start attempt, 120-second readiness wait, 10-second assertion, 180-second execution budget plus 40 seconds reserved cleanup, at most two service containers each limited to 1 CPU/512 MiB. Reject an expanded Compose model exceeding these bounds. No pulls, builds, pushes, credential changes, or volume deletion."

```sh
docker --context desktop-linux compose -f compose.yaml -p deepmodebot-container-check up --no-build --pull never --wait --wait-timeout 120 api
```

Before this command, inspect the full service/dependency/resource/mount model privately and reject external/shared data volumes, host-sensitive bind mounts, lifecycle hooks with unapproved effects, or missing caps. The resource caps are requirements on the reviewed configuration, not flags supplied by this command. Record resources created by this run. On success or failure, collect bounded diagnostics and, only for the newly owned project, tear down without deleting volumes:

```sh
docker --context desktop-linux compose -f compose.yaml -p deepmodebot-container-check down --timeout 20
```

`--wait-timeout` bounds readiness; `down --timeout` is a shutdown timeout, not total cleanup wall time. If cleanup fails, report remaining resource identities rather than claim success. Preserve all named/anonymous volumes; do not use `down -v`, global `system prune`/`volume prune`, or broad orphan removal. Volume removal requires separately authorized, identity-specific handling. Sources: [up](https://docs.docker.com/reference/cli/docker/compose/up/), [down](https://docs.docker.com/reference/cli/docker/compose/down/).

### Build-focused planning loop

Goal/self-prompt: "Review the existing Dockerfile for stage separation, cache invalidation, and secret handling. Freeze repository path, build context, named target, platform, builder endpoint, and output destination from repository evidence. Produce one minimal patch and one proposed build acceptance command; execute no build in this review. Cap: 15 minutes and two evidence/patch iterations. Stop with the exact missing prerequisite if builder identity or credential authority is unknown. Preserve all existing caches and volumes."

For an explicitly authorized execution variant, fix a wall-clock build budget and maximum attempts before invoking the selected builder; do not convert permission failures into retry loops or silently upload images/caches. Completion means the named artifact and acceptance check were observed, not merely that the build command was proposed.

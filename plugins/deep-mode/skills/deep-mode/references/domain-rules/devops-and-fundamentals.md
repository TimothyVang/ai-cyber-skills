# DevOps, tooling, and CS fundamentals

Read when working with Linux, the shell, git, Docker, Kubernetes, Terraform, CI/CD, deployments, or configuration and secrets, or when a bug turns on data structures, complexity, memory, floating point, concurrency, or networking protocols. Source keys are in `README.md`.

## Linux

- The kernel runs privileged and arbitrates CPU, RAM, disk, and network. User code runs in restricted user mode; an illegal memory access is a segmentation fault. (LINUX-CORE)
- One tree under `/`: devices in `/dev`, live process data in `/proc`, logs in `/var/log`, binaries in `/bin` and `/usr/bin`, config in `/etc`. (LINUX-DIRS)
- `systemd` is PID 1. It orders boot dependencies, restarts failed services, and collects logs (`journalctl`). `systemctl start` runs now; `systemctl enable` runs at boot. (SYSTEMD)
- Unix philosophy: small single-purpose tools joined by pipes. (UNIX-LINUX)
- Distros share the kernel and differ in package manager and policy: Debian/Ubuntu (`apt`, stability), Fedora (`dnf`, SELinux), Arch (`pacman`, minimal rolling), Kali (pentest tools). (DISTROS)
- Immutable distros (Fedora Silverblue, openSUSE Aeon) update the root image atomically with rollback; apps run as Flatpaks or containers. (DISTROS)
- A port names the service on a host: 80/443 web, 22 SSH. (LINUX-CORE)

## CLI tools

| Tool | Does |
|---|---|
| `fzf` | Fuzzy-find files, dirs, branches, containers, shell history (Ctrl+R) |
| `tmux` | Sessions that survive disconnects; panes and windows |
| `mosh` | SSH that survives IP changes, Wi-Fi drops, and sleep; local echo hides latency |
| `zoxide` | Jump to frequent dirs by partial name (`z portal`) |
| `bat` | `cat` with syntax highlighting, git gutter, line numbers |
| `btop` | Live CPU, memory, disk, network monitor |
| `ripgrep` (`rg`) | Fast recursive search that honors `.gitignore` and skips binaries |
| `fd` | Fast `find` that skips hidden and ignored paths |
| `delta` | Side-by-side, syntax-highlighted `git diff` pager |
| `lazydocker` | Terminal dashboard for containers, images, volumes |
| `yq` | Query and edit YAML, JSON, XML, CSV, TOML in scripts |
| `visidata` | Spreadsheet-style CSV and table browser in the terminal |
| `croc` | End-to-end encrypted, resumable file transfer between machines |
| `worktrunk` | Manage git worktrees (several branches checked out at once) |
| `dns-globe` | Watch DNS propagation across global resolvers |
| `gitlog` | Animated replay of a repo's commit history |
| `oxer` | One CLI for container status, resources, logs, restarts |
| `llm-fit` | Score which local models your RAM, VRAM, and GPU can run |
| `gre` | Generate a regex from example strings |
| `condo` | Find and purge stale build artifacts and `node_modules` |

(LINUX-10, CLI-TOOLS)

## Git

- A commit is an immutable snapshot of the whole tree. A branch is a cheap pointer to a commit. (GITHUB)
- A PR is the review gate: diff review, suggestions, CI checks before merge. (GITHUB)
- A merge conflict means two branches changed the same lines; reconcile them by hand. (DEV-LIFE)
- Worktrees check out several branches into separate directories at once, with no stash juggling. (CLI-TOOLS)

## Containers

- A container bundles code, runtime, system libraries, and dependencies, and runs the same in dev, staging, and prod. (DOCKER)
- An image is an immutable template built from a Dockerfile and stored in a registry. A container is a running instance of it. (DEV-LIFE)
- Containers are host processes isolated by namespaces (process, mount, network) and limited by cgroups (CPU, memory). They are not VMs. (LINUX-CORE)
- Docker runs through a daemon. Podman is daemonless and rootless. Both run OCI images. Compose runs multi-container stacks locally. (PODMAN)

## Kubernetes

- Orchestrates many containerized services across a cluster: scheduling, health, scaling. (K8S)
- Declarative: you state the desired state in YAML (for example 3 replicas) and control loops keep reconciling reality to it. (K8S)
- Self-healing: crashed containers and failed nodes get their pods rescheduled onto healthy nodes. (K8S)
- Services get stable internal DNS names and virtual IPs and load-balance across their pods. (K8S)

## Terraform

- Infrastructure as code in HCL: versioned, reviewed, and tested like app code. (TERRAFORM)
- Providers talk to platform APIs (AWS, Azure, GCP, GitHub). Resources declare the components. (TERRAFORM)
- State maps config to real resources. Keep it in a remote backend with state locking so concurrent runs cannot corrupt it. (TERRAFORM)
- Always `terraform plan` (preview create, change, destroy) before `terraform apply`. (TERRAFORM)
- Drift: a manual console change gets reverted by the next plan unless the code is updated to match. (TERRAFORM)

## CI/CD and deployment

- CI (Jenkins, GitHub Actions, GitLab CI) runs build, lint, and tests on every commit or PR. (JENKINS)
- Continuous delivery: always deployable, release behind an approval gate. Continuous deployment: every green change ships automatically. (DEV-LIFE)
- Pipelines live in versioned files (`Jenkinsfile`, Actions YAML), not GUI config. (JENKINS)
- Build once into an immutable artifact or image and promote that same artifact through environments. Never rebuild per environment. (DEVOPS-2)
- Airflow runs scheduled data pipelines as DAGs with retries, dependency checks, and backfill of historical partitions. (AIRFLOW)
- Ansible configures fleets agentlessly over SSH or WinRM with YAML playbooks. (ANSIBLE)

Deployment strategies (DEVOPS-INT):

| Strategy | How | Trade-off |
|---|---|---|
| Big bang | Everyone switches at once | Simple, all-or-nothing risk |
| Recreate | Stop old, then start new | Downtime |
| Rolling | Replace instances a few at a time | Mixed versions during rollout |
| Blue/green | Two full environments, flip traffic | Instant rollback, double capacity |
| Canary | Small traffic slice first, watch metrics | Safest, needs good metrics |

- Feature flags separate deploy from release; a bad feature turns off in seconds. (DEV-LIFE)
- Secrets and environment-specific endpoints never live in code. Inject them at runtime from env vars or a secrets vault. (DEV-LIFE)
- API changes stay backward compatible: add optional fields; rename or remove only behind a new version with a deprecation window. (DEV-LIFE)
- DevOps is shared ownership of stability between dev and ops, through automation and fast feedback. (DEVOPS)
- Metrics with Prometheus and Grafana, centralized logs, and distributed traces across service hops. (DEVOPS)

## CS fundamentals

- Stack: fast, fixed-size, LIFO frames for locals. Heap: dynamic data that lives until freed or collected. (CS-4H)
- Stack overflow is recursion deeper than the stack. A memory leak is heap objects still referenced by something long-lived. (CS-4H)
- In Java and Python, assignment and argument passing copy the reference; mutating through one name changes the shared object. (CS-4H)
- A shallow copy shares nested objects. A deep copy clones everything recursively. (CS-4H)
- Big O ranks growth: O(log N) < O(N) < O(N log N) < O(N²) < O(N!). (CS-4H)
- Arrays: contiguous memory, O(1) index, cache-friendly. Linked lists: O(1) insert at a known node, slow indexing. (CS-4H)
- Stack (LIFO) for undo and bracket matching. Queue (FIFO) for fair scheduling and jobs. (CS-4H)
- Hash maps give O(1) average lookup; collisions resolve by chaining or open addressing. (CS-4H)
- Binary search halves a sorted range per step, O(log N). Balanced trees keep order for range queries. (CS-4H)
- Heaps give O(1) peek at the min or max and O(log N) insert, which is how priority queues work. (CS-4H)
- BFS (queue) explores level by level. DFS (stack or recursion) goes deep down one branch. (CS-4H)
- Dynamic programming: split into overlapping subproblems and memoize to kill exponential rework. (CS-4H)
- Two pointers walk a sorted array from both ends for O(N) pair finding. A sliding window keeps a running result over a contiguous range. (DSA-5)
- Floats are base-2, so 0.1 + 0.2 is not exactly 0.3. Store money as integer cents. (CS-4H)
- AOT compiles to native ahead of time, an interpreter runs code as it reads it, and a JIT compiles hot bytecode at runtime. (PROGRAMMING)
- Race condition: unsynchronized read-modify-write on shared memory loses updates. Fix with a mutex, semaphore, or atomic. (CS-4H)
- An async event loop (Node, asyncio) handles thousands of concurrent I/O waits on one thread but cannot speed up CPU-bound work. (CS-4H)

## Networking fundamentals

OSI layers, bottom up, used as a troubleshooting ladder (OSI):

| # | Layer | Unit and gear |
|---|---|---|
| 1 | Physical | Bits, cables |
| 2 | Data link | MAC frames, switches |
| 3 | Network | IP packets, routers |
| 4 | Transport | TCP and UDP segments |
| 5 | Session | Session management |
| 6 | Presentation | Encryption, formatting |
| 7 | Application | HTTP, DNS |

- IP gives logical addresses; routers forward by routing table. (PROTOCOLS)
- TCP: 3-way handshake; ordered, checked delivery with retransmits. UDP: connectionless, minimal overhead, used for live media and DNS. (PROTOCOLS)
- DNS is a distributed hierarchy from names to IPs; TTL controls caching at resolvers. (PROTOCOLS)
- DHCP hands a new device its IP, subnet mask, gateway, and DNS servers. (PROTOCOLS)
- HTTPS is HTTP inside TLS: a certificate-based handshake authenticates the server, then the session is encrypted. (PROTOCOLS)
- SSH authenticates with key pairs over port 22 and carries encrypted shells and file transfers (SCP, SFTP). (SSH)
- NAT rewrites addresses at a boundary so a private fleet shares public IPv4. (AWS-NET)
- A VPN tunnels encrypted private traffic over a public network. (PROTOCOLS)

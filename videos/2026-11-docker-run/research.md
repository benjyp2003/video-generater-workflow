# Research — What happens when you run docker run?

Sources live in `sources.yaml`. Every claim must cite source ids.
Status: `verified` (you checked the primary source) · `assumption` (must be verified
or cut before Gate 1) · `rejected` · `deprecated`.

> Draft ledger. Every claim is `assumption` until you open its sources and
> confirm. Wording is deliberately cautious ("by default", "typically").

## Claims ledger
| id | claim | sources | status | notes |
|----|-------|---------|--------|-------|
| C1 | The `docker` command is a client; it sends requests to the Docker daemon (`dockerd`) through the Docker Engine REST API | S1 | assumption | |
| C2 | On Linux, by default the client reaches the daemon through the Unix socket `/var/run/docker.sock` | S3 | assumption | Docker Desktop and remote contexts differ; say "on Linux, by default" |
| C3 | If the image is not available locally, `docker run` pulls it from a registry first; by default that registry is Docker Hub | S1, S2 | assumption | `--pull` flag changes this |
| C4 | Images are made of read-only layers; a running container adds a thin writable layer on top | S9 | assumption | |
| C5 | On most current Linux installs the storage is handled by overlay filesystem layering (overlay2 driver or the containerd image store / snapshotter) | S9, S11 | assumption | Version-dependent: newer Engine releases default to the containerd image store on fresh installs — check for the version you demo and phrase accordingly |
| C6 | `dockerd` delegates container lifecycle management to `containerd` | S1, S4 | assumption | |
| C7 | containerd uses an OCI runtime, `runc` by default, via a per-container shim process | S4, S5 | assumption | Check the shim naming for the version shown |
| C8 | runc creates the container according to the OCI runtime specification | S5, S6 | assumption | |
| C9 | Isolation comes from Linux namespaces (e.g. PID, network, mount, UTS, IPC); each restricts what the process can see | S7 | assumption | User namespaces are not enabled by default in Docker — don't list them as always used |
| C10 | Resource limits (CPU, memory, PIDs) are enforced with control groups (cgroups) | S8, S2 | assumption | |
| C11 | By default a container is attached to the default bridge network and gets its own network interface (a veth pair connected to the docker0 bridge) | S10 | assumption | Confirm with `ip addr` / `docker network inspect bridge` in the demo |
| C12 | The container's main process is the command from the image (or the one you pass) and runs as PID 1 inside its PID namespace; when it exits, the container stops | S2, S7 | assumption | |
| C13 | A container is a regular Linux process on the host with isolation applied, not a virtual machine with its own kernel | S1, S7 | assumption | Core misconception (see below) |
| C14 | `--rm` removes the container automatically when it exits | S2 | assumption | |

## Misconceptions to address
- "A container is a lightweight VM." → It shares the host kernel (C13).
- "`docker run` always downloads the image." → Only when it's not local (C3).
- "Docker does the isolation itself." → The kernel does; Docker orchestrates (C9, C10).

## Version notes
- Record `docker version` (client + server), containerd and runc versions from the
  demo log into video.yaml `tech_versions`.
- Storage wording (C5) depends on Engine version and install type.

## Open questions
- Show `ps` on the host to prove it's a normal process? Needs a VM/Linux host,
  not Docker Desktop — decide based on the demo environment.

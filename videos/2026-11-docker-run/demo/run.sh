#!/usr/bin/env bash
# Run commands.sh in a disposable sandbox and save a timestamped log.
#
# Default sandbox: Docker-in-Docker (privileged, throwaway) so demos that use
# `docker` work without touching your host daemon. For demos that don't need
# Docker, set SANDBOX_IMAGE=ubuntu:24.04 (unprivileged).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
image="${SANDBOX_IMAGE:-docker:dind}"
log="$here/logs/$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$here/logs"

if [[ "$image" == docker:dind* ]]; then
  name="demo-sandbox-$$"
  trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
  docker run -d --rm --privileged --name "$name" -h demo \
    -v "$here:/demo:ro" "$image" >/dev/null
  # wait for the inner daemon
  for _ in $(seq 1 30); do docker exec "$name" docker info >/dev/null 2>&1 && break; sleep 1; done
  docker exec "$name" sh -c 'docker version; echo ---; sh -x /demo/commands.sh' 2>&1 | tee "$log"
else
  docker run --rm -h demo -v "$here:/demo:ro" "$image" sh -x /demo/commands.sh 2>&1 | tee "$log"
fi
echo "log saved: $log"

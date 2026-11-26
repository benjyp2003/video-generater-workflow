#!/usr/bin/env sh
# Commands shown on screen, in order. Runs INSIDE the sandbox (see run.sh).
set -eu
docker run --rm hello-world
# Evidence for the claims (shown or referenced in the video):
docker info --format 'storage={{.Driver}} runtime={{.DefaultRuntime}} cgroup={{.CgroupVersion}}'
docker network inspect bridge --format '{{.Name}} {{(index .IPAM.Config 0).Subnet}}'
docker run --rm alpine:3.20 sh -c 'echo "PID inside: $$"; ls /proc | grep -E "^[0-9]+$"'
docker run --rm alpine:3.20 ip addr show

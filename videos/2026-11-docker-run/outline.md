# Outline — What happens when you run docker run?

Format: concept (see templates/formats.md). Target ≈ 8 min (~1,150 words).

| scene | idea | claims | visual | ~sec |
|-------|------|--------|--------|------|
| s01 Hook | One command, a running isolated process in a second — what happened? | — | slide:title, terminal:run-hello | 25 |
| s02 Client and daemon | `docker` is a client; dockerd does the work via an API over a socket | C1, C2 | diagram:cli-daemon | 50 |
| s03 Finding the image | local check → pull from registry if missing | C3 | diagram:pull-flow | 45 |
| s04 Layers | read-only layers + thin writable layer | C4, C5 | diagram:layers | 50 |
| s05 Handing off | dockerd → containerd → shim → runc | C6, C7, C8 | diagram:runtime-stack | 60 |
| s06 Namespaces | what the process can see | C9 | diagram:namespaces | 60 |
| s07 Cgroups | what the process can use | C10 | slide:cgroups | 40 |
| s08 Network | default bridge, veth, docker0 | C11 | diagram:network | 45 |
| s09 The process runs | PID 1, exits → container stops, --rm | C12, C14 | terminal:run-hello | 45 |
| s10 Misconception | not a VM: shared kernel | C13 | slide:not-a-vm | 40 |
| s11 Recap | three-step summary + next video | — | diagram:runtime-stack | 30 |

---
schema_version: 1
video: 2026-11-docker-run
---

## s01 Hook
[VISUAL] slide:title
[VISUAL] terminal:run-hello
[CMD] docker run --rm hello-world
You type one short command. A moment later, a program is running in its own isolated little world, and then it's gone. But what actually happened in between? In the next few minutes, we'll follow that command step by step, from your keyboard all the way down to the Linux kernel.

## s02 Client and daemon
[VISUAL] diagram:cli-daemon
[CLAIM] C1, C2
The first surprise is that the docker command you type doesn't run containers at all. It's a client. Its job is to turn your command into an API request and send it to a background service called the Docker daemon, dockerd. On Linux, by default, that request travels through a local socket file at slash var slash run slash docker dot sock. The daemon is the part that does the real work. That split is why the same client can also talk to a daemon on another machine.

## s03 Finding the image
[VISUAL] diagram:pull-flow
[CLAIM] C3
The daemon's first question is: do I already have this image? An image is the packaged filesystem and settings your container starts from. If it's already on your machine, Docker uses it. If not, the daemon pulls it from a registry first. By default, that registry is Docker Hub. That's why the very first run of an image is slow, and the second one is almost instant.

## s04 Layers
[VISUAL] diagram:layers
[CLAIM] C4, C5
An image isn't one big file. It's a stack of read-only layers, each one adding or changing files. When a container starts, Docker doesn't copy those layers. It stacks them and adds one thin, writable layer on top, just for this container. Anything the container changes goes into that top layer. On most Linux setups today, this stacking is done with an overlay filesystem. That's why starting a container is fast, and why ten containers from the same image don't need ten copies of it.

## s05 Handing off
[VISUAL] diagram:runtime-stack
[CLAIM] C6, C7, C8
Now the daemon is ready to create the container, but it doesn't do that by itself either. It hands the job to another component called containerd, which manages the container's lifecycle. containerd, in turn, starts a small shim process and asks a low-level runtime to create the container. By default, that runtime is runc. runc follows a public standard, the Open Container Initiative runtime specification. So the chain is: client, dockerd, containerd, shim, runc. Each piece has one job.

## s06 Namespaces
[VISUAL] diagram:namespaces
[CLAIM] C9
Here's the key idea. runc doesn't build a virtual machine. It asks the Linux kernel to start a normal process, but inside a set of namespaces. A namespace limits what a process can see. With its own PID namespace, the process sees only its own process list. With its own network namespace, it gets its own network interfaces. With its own mount namespace, it sees its own filesystem. Hostname and inter-process communication get their own namespaces too. Same kernel, different view.

## s07 Cgroups
[VISUAL] slide:cgroups
[CLAIM] C10
Namespaces control what a process can see. Control groups, or cgroups, control what it can use. Through cgroups, the kernel can limit how much memory, CPU time, and how many processes a container is allowed. When you pass a flag like dash dash memory, this is the mechanism that enforces it.

## s08 Network
[VISUAL] diagram:network
[CLAIM] C11
What about networking? Unless you say otherwise, the container joins Docker's default bridge network. Docker creates a virtual cable called a veth pair. One end becomes the container's network interface. The other end plugs into a virtual switch on the host called docker0. That's how the container gets its own IP address and can still reach the outside world.

## s09 The process runs
[VISUAL] terminal:run-hello
[CLAIM] C12, C14
[CMD] docker run --rm hello-world
Finally, runc starts the command from the image. Inside its PID namespace, that process is PID 1, the first and most important process. For hello world, the program prints its message and exits. And when the main process exits, the container stops. Because we used dash dash rm, Docker then removes the stopped container automatically.

## s10 Not a virtual machine
[VISUAL] slide:not-a-vm
[CLAIM] C13
This is why a container is not a lightweight virtual machine. A virtual machine boots its own kernel. A container is a regular process on the host, sharing the host's kernel, with namespaces and cgroups wrapped around it. That's what makes containers so fast to start, and it's also why a Linux container needs a Linux kernel underneath.

## s11 Recap
[VISUAL] diagram:runtime-stack
So, when you type docker run: first, the client sends an API request to the daemon. Second, the daemon makes sure the image is available and prepares its layers. Third, containerd and runc ask the kernel for an isolated, limited process, and your program runs. In the next video, we'll build our own image with a Dockerfile.

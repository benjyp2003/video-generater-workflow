# Reproducible terminal recording for scenes s01 and s09.
# Rendered with: make terminal V=videos/2026-11-docker-run
# Runs on the recording machine: only use inside a disposable VM/sandbox.
Output run-hello.mp4
Set FontFamily "JetBrains Mono"
Set FontSize 28
Set Width 1920
Set Height 1080
Set Theme "Catppuccin Mocha"
Set TypingSpeed 60ms
Set Shell bash
Env PS1 "user@demo:~$ "

Type "docker run --rm hello-world"
Sleep 500ms
Enter
Sleep 8s

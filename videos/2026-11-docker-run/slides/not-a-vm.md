---
marp: true
theme: studio
---

## A container is *not* a lightweight VM

| Virtual machine | Container |
|---|---|
| boots its **own kernel** | shares the **host kernel** |
| virtual hardware | a normal process + namespaces + cgroups |
| starts in seconds–minutes | starts in milliseconds–seconds |

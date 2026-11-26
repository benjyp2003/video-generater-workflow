# Research prompt

You are helping research a beginner-friendly technical YouTube video.

Topic: {{topic}}
Audience: {{audience}}
Format: {{format}}

Tasks:
1. List the 6–12 key factual claims the video must make, in the order a beginner
   needs them. Number them C1, C2, …
2. For each claim, name the **official primary source** where it can be verified
   (vendor documentation, specification, man page, or source code). Give the page
   title and URL. If you are not sure a URL exists, say "URL unknown — search for: <query>".
   Do not invent URLs.
3. Flag each claim as: stable / version-dependent / configurable-default.
   For version-dependent claims, say what version info must be recorded.
4. List 2–4 common beginner misconceptions about this topic.
5. List anything deprecated or recently changed that a video from a few years ago
   would get wrong.

Output format (Markdown):

## Claims ledger
| id | claim | candidate source (title + URL) | kind | status |
(status is always `assumption` — a human will verify)

## Misconceptions
## Recent changes / deprecations
## Open questions

Do not write a script. Do not state anything as verified.

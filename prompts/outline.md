# Outline prompt

Create an outline for a {{format}} video, target length {{target_length_min}} minutes,
for: {{audience}}.

Use ONLY the claims in this verified ledger. If a needed fact is missing, list it
under "Missing claims" instead of inventing it.

<source name="research.md">
{{research_md}}
</source>

Format structure to follow:
{{format_structure}}

Output: a numbered list of scenes. For each scene give:
- scene id (s01, s02, …) and title
- the one idea it teaches
- claim ids used
- suggested visual: diagram:<name> | slide:<name> | terminal:<name> | screen:<name>
- approximate duration in seconds (narration ≈ 150 words/minute)

Then: "Missing claims" and "Misconceptions addressed".

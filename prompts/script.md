# Script prompt

Write narration for this video following the channel style guide exactly.

<source name="channel/style.md">
{{style_md}}
</source>

<source name="outline.md">
{{outline_md}}
</source>

<source name="research.md">
{{research_md}}
</source>

Output rules (the file is parsed by tools — follow the format exactly):
- One scene per `## sNN Title` heading, using the ids from the outline.
- Directly under the heading, marker lines, each on its own line:
  - `[VISUAL] <type>:<name> <optional note>` (one or more)
  - `[CLAIM] C1, C3` for every claim the scene relies on
  - `[CMD] <command>` for every command shown on screen
- Then the narration as plain paragraphs. No markdown formatting inside narration,
  no stage directions, no emoji. Max ~120 words per scene.
- Spell out symbols as they should be spoken only where it aids clarity
  (e.g. "slash var slash run").
- Do not add facts that are not in the research ledger.

After the script, list every sentence you were unsure about.

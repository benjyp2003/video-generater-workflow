# Metadata prompt

Draft YouTube metadata for this video.

<source name="script.md">
{{script_md}}
</source>

<source name="video.yaml">
{{video_yaml}}
</source>

Produce:
1. 5 title options (≤ 60 characters preferred, no clickbait the video doesn't pay off,
   include the main keyword naturally).
2. A description:
   - 2-sentence summary first (shown above the fold).
   - Chapters `00:00 Title` using the scene list (a human will fix timestamps).
   - "Versions shown:" line from tech_versions.
   - "Sources:" list (titles + URLs from the research ledger only).
3. 5–10 tags.
4. 3 thumbnail text options (≤ 4 words).

Output as YAML matching publish.yaml fields: title_alternatives, description, tags,
plus `thumbnail_text_options`.

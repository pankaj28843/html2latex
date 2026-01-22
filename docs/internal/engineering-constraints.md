# Engineering Constraints

## Repository hygiene
- Keep tracked files and PR descriptions free of local filesystem paths.
- Avoid including internal planning artifacts or draft notes in the repository.
- Document behavior and guarantees in user-facing docs only.

## Architecture constraints
- Use JustHTML for HTML parsing (no lxml).
- Require Tectonic for LaTeX integration tests; no fallback engines.
- Keep the public API small and explicit; prioritize deterministic output.

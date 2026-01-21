# Golden Fixtures

These fixtures are used to lock HTML→LaTeX output behavior during modernization.

- Source of truth: `cases.json`
- Each case contains `name`, `html`, and `expected`.
- Expected outputs are based on current template semantics and may be adjusted after Python 3 + justhtml migration.

Notes:
- Whitespace and line endings may be normalized in future tests.
- The goal is to detect unintended output drift once the new parser is wired in.

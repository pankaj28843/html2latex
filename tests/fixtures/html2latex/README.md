# HTML2LaTeX fixture corpus

Each fixture lives as a paired `.html` and `.tex` file with the same name.
Fixtures are organized by feature area so they are easy to find and reuse.

## Layout

- `blocks/` — block-level constructs (paragraphs, headings, blockquote, pre, hr, tables)
- `inline/` — inline formatting and spans
- `lists/` — list structures
- `errors/` — invalid inputs used for diagnostics tests (not part of strict golden runs)
- `inline/semantic/` — inline semantic tags that preserve content
- `blocks/semantic/` — block containers that preserve child content

## Conventions

- Files are UTF-8, LF endings, and end with a trailing newline.
- No tabs; keep indentation minimal and readable.
- Keep fixtures small and focused; prefer one behavior per case.
- Names are semantic (what the case demonstrates), not numeric.
- HTML fixtures are formatted with Prettier; error fixtures are excluded.
- The Prettier config is tuned for readability (100-column width, CSS whitespace handling).
- `.tex` fixtures should compile with Tectonic in isolation (see `CONTRIBUTING.md`).

## Adding a new case

1. Create a new `case-name.html` file in the right feature folder.
2. Create a matching `case-name.tex` with expected LaTeX output.
3. Ensure both files are formatted and include a trailing newline.

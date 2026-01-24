# HTML2LaTeX fixture corpus

Each fixture lives as a paired `.html` and `.tex` file with the same name.
Fixtures are organized by feature area so they are easy to find and reuse.

## Layout

- `blocks/` — block-level constructs (paragraphs, headings, blockquote, pre, hr, tables, figures)
- `inline/` — inline formatting, spans, and quotes
- `lists/` — list structures (ul, ol, dl with various attributes)
- `errors/` — invalid inputs used for diagnostics tests (not part of strict golden runs)
- `inline/semantic/` — inline semantic tags that preserve content
- `inline/quote/` — inline quote element with nesting support
- `blocks/semantic/` — block containers that preserve child content
- `e2e-wysiwyg/` — end-to-end WYSIWYG editor output samples

## Conventions

- Files are UTF-8 with LF line endings.
- No tabs; keep indentation minimal and readable.
- Keep fixtures small and focused; prefer one behavior per case.
- Names are semantic (what the case demonstrates), not numeric.
- All HTML and LaTeX fixtures are formatted with Prettier (2-space indentation).
- The Prettier config is tuned for readability (100-column width, CSS whitespace handling).
- `.tex` fixtures should compile with Tectonic in isolation (see `CONTRIBUTING.md`).
- All non-error fixture pairs are exercised in `tests/integration/test_fixture_corpus.py`.

## Formatting example

Prefer clean, readable structure that reflects nesting:

```html
<ol>
  <li>
    Outer
    <ul>
      <li>Inner</li>
    </ul>
  </li>
</ol>
```

## Adding a new case

1. Create a new `case-name.html` file in the right feature folder.
2. Create a matching `case-name.tex` with expected LaTeX output.
3. Run `npx prettier --write "path/to/case-name.html" "path/to/case-name.tex"` to format.

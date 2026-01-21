# Diagnostics + Strict Mode Design (Step 0.5)

Date: 2026-01-21
Scope: Error taxonomy, structured diagnostics, and strict-mode behavior

## Goals
- Provide structured, machine-readable diagnostics from parse -> transform -> render.
- Enable optional strict mode to fail fast on unsafe or invalid outputs.
- Keep default behavior backward compatible (best-effort rendering).

## Proposed error model
### DiagnosticEvent (dataclass)
Fields:
- `code`: short string (kebab-case), stable identifier.
- `category`: one of `parse`, `transform`, `render`, `asset`, `latex`, `config`, `safety`.
- `severity`: `info`, `warn`, `error`, `fatal`.
- `message`: human-friendly message.
- `location`: optional `{line, column, end_column, node_path}`.
- `source_html`: optional snippet or full input (for strict mode exceptions).
- `context`: dict for tag name, attribute, file path, template name, etc.

### Error taxonomy (initial draft)
- `parse/*`: tokenizer + treebuilder errors from JustHTML.
- `transform/*`: normalization (inline styles, math parsing, whitespace fixes).
- `render/*`: template selection failures, missing templates, render exceptions.
- `asset/*`: image download failures, missing local assets, size probe errors.
- `latex/*`: invalid LaTeX output, injection risk, invalid escape sequences.
- `config/*`: invalid options or incompatible settings.
- `safety/*`: unsafe HTML content or blocked tags/attributes.

## Integration points
1) Parsing
- Update `parse_html` to accept `collect_errors=True` and `strict=True` flags.
- Capture JustHTML `ParseError` objects and map to `DiagnosticEvent`:
  - `code`: parse error code (from JustHTML)
  - `category`: `parse`
  - `location`: line/column from ParseError
  - `message`: use JustHTML error message helper

2) Transform and render
- Instrument normalization + inline style application to emit `transform/*` errors when:
  - Unsupported CSS value types
  - Invalid numeric parsing or unit conversion
- Template rendering:
  - `render/template-not-found`
  - `render/template-error`

3) Assets + LaTeX
- Image handling:
  - `asset/download-failed`
  - `asset/invalid-dimensions`
- LaTeX validation (tectonic):
  - `latex/compile-error`
  - `latex/unsafe-output` (e.g., unescaped input detected)

## Strict mode behavior
- `strict=True` raises a `DiagnosticsError` if any `error` or `fatal` events exist.
- `strict=False` returns best-effort output + diagnostics list (if requested).
- Option: `return_diagnostics=True` to return `(output, diagnostics)`.

### Strict-mode policy
- Fail on any of:
  - `parse/*` (unless explicitly downgraded)
  - `render/*`
  - `latex/*`
  - `safety/*`
- Continue on `transform/*` warnings and most `asset/*` errors if output remains valid.

## Thread-safety + performance
- Use a per-call diagnostics collector (no global mutable lists).
- If collection is disabled, emit nothing to avoid overhead.

## Proposed API additions
- `html2latex(html: str, *, strict: bool = False, return_diagnostics: bool = False, collect_diagnostics: bool | None = None) -> str | tuple[str, list[DiagnosticEvent]]`
- `DiagnosticsError(Exception)` with:
  - `.events` list
  - `.first_error` property

## Test plan (hooks into Step 2.6)
- Unit tests for mapping JustHTML `ParseError` -> `DiagnosticEvent`.
- Strict-mode tests:
  - parse error triggers exception
  - render error triggers exception
  - asset warning does not fail unless severity escalated

## Open questions
- Should strict mode default to `error` only or `error` + `warn`?
- Should we expose a logger handler for diagnostics in addition to return values?


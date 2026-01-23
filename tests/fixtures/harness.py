import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

FIXTURE_ROOT = Path(__file__).resolve().parent / "html2latex"


@dataclass(frozen=True)
class FixtureCase:
    case_id: str
    html: str
    tex: str
    html_path: Path
    tex_path: Path


def _normalize_text(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    return "\n".join(line.rstrip() for line in stripped.splitlines())


def _find_matching_brace(s: str, start: int) -> int:
    """Find the position of the matching closing brace.

    Args:
        s: The string to search
        start: Position of the opening brace

    Returns:
        Position of matching closing brace, or -1 if not found
    """
    if start >= len(s) or s[start] != "{":
        return -1
    depth = 1
    pos = start + 1
    while pos < len(s) and depth > 0:
        if s[pos] == "{":
            depth += 1
        elif s[pos] == "}":
            depth -= 1
        pos += 1
    return pos - 1 if depth == 0 else -1


def _remove_space_after_commands(tex: str, commands: list[str]) -> str:
    """Remove spaces after specific commands that have brace arguments.

    This handles nested braces properly.
    """
    pattern = re.compile(r"\\(" + "|".join(re.escape(cmd) for cmd in commands) + r")\{")
    result = []
    last_end = 0

    for match in pattern.finditer(tex):
        brace_start = match.end() - 1  # Position of the first opening brace
        pos = brace_start

        # Find all consecutive brace groups
        while pos < len(tex) and tex[pos] == "{":
            brace_end = _find_matching_brace(tex, pos)
            if brace_end == -1:
                break
            pos = brace_end + 1

        # Add everything up to and including all brace groups
        result.append(tex[last_end:pos])

        # Skip any whitespace after the closing braces
        while pos < len(tex) and tex[pos] in " \t\n":
            pos += 1

        last_end = pos

    # Add remaining content
    result.append(tex[last_end:])
    return "".join(result)


def _remove_space_after_section_braces(tex: str) -> str:
    """Remove spaces after section command closing braces."""
    return _remove_space_after_commands(
        tex,
        ["section", "subsection", "subsubsection", "paragraph", "subparagraph"],
    )


def _normalize_latex_whitespace(tex: str) -> str:
    """Normalize LaTeX whitespace for comparison.

    In LaTeX, source whitespace (newlines, leading spaces) does not affect
    rendered output in most contexts. This function normalizes formatting
    differences so that semantically identical LaTeX compares equal.
    """
    # Preserve verbatim environments exactly
    verbatim_pattern = r"(\\begin\{verbatim\}.*?\\end\{verbatim\})"
    verbatim_blocks: list[str] = []

    def save_verbatim(match: re.Match[str]) -> str:
        verbatim_blocks.append(match.group(1))
        return f"__VERBATIM_{len(verbatim_blocks) - 1}__"

    tex = re.sub(verbatim_pattern, save_verbatim, tex, flags=re.DOTALL)

    # Normalize math delimiters: $...$ -> \(...\) and $$...$$ -> \[...\]
    # Use a simple approach for non-nested math
    tex = re.sub(r"\$\$([^$]+)\$\$", r"\\[\1\\]", tex)
    tex = re.sub(r"\$([^$]+)\$", r"\\(\1\\)", tex)

    # Remove unnecessary braces around single characters in math (e.g., x^{2} -> x^2)
    # This handles both exponents and subscripts
    tex = re.sub(r"(\^|_)\{([a-zA-Z0-9])\}", r"\1\2", tex)

    # Normalize whitespace: collapse multiple spaces/newlines to single space
    tex = re.sub(r"\s+", " ", tex)

    # Remove spaces before and after \end{...}
    tex = re.sub(r"\s*(\\end\{[^}]+\})\s*", r"\1", tex)

    # Remove spaces before and after \begin{...}[...]{...}
    tex = re.sub(r"\s*(\\begin\{[^}]+\}(?:\[[^\]]*\])?(?:\{[^}]*\})*)\s*", r"\1", tex)

    # Remove spaces before \item
    tex = re.sub(r"\s+(\\item)", r"\1", tex)

    # Normalize \item whitespace to single space (item needs space before its content)
    tex = re.sub(r"(\\item)\s+", r"\1 ", tex)

    # Remove spaces after section command closing braces
    tex = _remove_space_after_section_braces(tex)

    # Normalize space after \par to single space
    tex = re.sub(r"(\\par)\s+", r"\1 ", tex)

    # Remove spaces before and after line-break commands (\newline, \\, \linebreak)
    tex = re.sub(r"\s*(\\newline|\\\\|\\linebreak)\s*", r"\1", tex)

    # Remove spaces before and after \caption{...}
    tex = re.sub(r"\s*(\\caption\{[^}]*\})\s*", r"\1", tex)

    # Remove spaces after commands with nested braces
    tex = _remove_space_after_commands(
        tex,
        [
            "renewcommand",
            "setcounter",
            "setlength",
            "addtocounter",
            "href",
            "textbf",
            "textit",
            "texttt",
            "underline",
            "emph",
        ],
    )

    # Remove spaces before commands that typically appear after content
    tex = re.sub(
        r"\s+(\\(?:addtocounter|includegraphics|setcounter|renewcommand|"
        r"section|subsection|subsubsection|paragraph|subparagraph))",
        r"\1",
        tex,
    )

    # Normalize spaces inside display math \[...\] - remove leading/trailing spaces
    tex = re.sub(r"\\\[\s+", r"\\[", tex)
    tex = re.sub(r"\s+\\\]", r"\\]", tex)

    # Normalize spaces inside inline math \(...\) - remove leading/trailing spaces
    tex = re.sub(r"\\\(\s+", r"\\(", tex)
    tex = re.sub(r"\s+\\\)", r"\\)", tex)

    # Restore verbatim blocks
    for i, block in enumerate(verbatim_blocks):
        tex = tex.replace(f"__VERBATIM_{i}__", block)

    return tex.strip()


def normalize_fixture_text(value: str) -> str:
    """Normalize LaTeX text for comparison, accounting for formatting differences."""
    return _normalize_latex_whitespace(value)


def _validate_text(path: Path, text: str) -> None:
    if not text.strip():
        raise ValueError(f"Fixture is empty: {path}")
    # Note: prettier-plugin-latex doesn't add trailing newlines, so we don't require them


def _case_id_for(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return rel.as_posix()


@lru_cache(maxsize=1)
def _load_all_cases() -> tuple[FixtureCase, ...]:
    if not FIXTURE_ROOT.exists():
        raise FileNotFoundError(f"Fixture root not found: {FIXTURE_ROOT}")

    html_files = sorted(p for p in FIXTURE_ROOT.rglob("*.html") if p.is_file())
    tex_files = sorted(p for p in FIXTURE_ROOT.rglob("*.tex") if p.is_file())

    html_keys = {_case_id_for(p, FIXTURE_ROOT): p for p in html_files}
    tex_keys = {_case_id_for(p, FIXTURE_ROOT): p for p in tex_files}

    missing_tex = sorted(set(html_keys) - set(tex_keys))
    missing_html = sorted(set(tex_keys) - set(html_keys))
    if missing_tex or missing_html:
        problems = []
        if missing_tex:
            problems.append(f"Missing .tex for: {', '.join(missing_tex)}")
        if missing_html:
            problems.append(f"Missing .html for: {', '.join(missing_html)}")
        raise AssertionError("Fixture pairs mismatch: " + "; ".join(problems))

    cases: list[FixtureCase] = []
    for case_id in sorted(html_keys):
        html_path = html_keys[case_id]
        tex_path = tex_keys[case_id]
        html = html_path.read_text(encoding="utf-8")
        tex = tex_path.read_text(encoding="utf-8")
        _validate_text(html_path, html)
        _validate_text(tex_path, tex)
        cases.append(
            FixtureCase(
                case_id=case_id,
                html=html,
                tex=tex,
                html_path=html_path,
                tex_path=tex_path,
            )
        )

    return tuple(cases)


def load_fixture_cases(
    filters: list[str] | None = None,
    *,
    include_errors: bool = True,
) -> list[FixtureCase]:
    cases = list(_load_all_cases())
    if not include_errors:
        cases = [case for case in cases if not case.case_id.startswith("errors/")]
    if not filters:
        return cases
    return [case for case in cases if any(case.case_id.startswith(prefix) for prefix in filters)]


def get_fixture_case(case_id: str) -> FixtureCase:
    for case in _load_all_cases():
        if case.case_id == case_id:
            return case
    raise KeyError(f"Fixture not found: {case_id}")

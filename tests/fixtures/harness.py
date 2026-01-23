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
    if "\t" in text:
        raise ValueError(f"Fixture contains tabs: {path}")
    if not text.endswith("\n"):
        raise ValueError(f"Fixture must end with a newline: {path}")


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

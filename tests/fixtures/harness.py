from __future__ import annotations

from dataclasses import dataclass
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


def normalize_fixture_text(value: str) -> str:
    return _normalize_text(value)


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


def load_fixture_cases(filters: list[str] | None = None) -> list[FixtureCase]:
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

    if filters:
        filtered = []
        for case in cases:
            if any(case.case_id.startswith(prefix) for prefix in filters):
                filtered.append(case)
        return filtered

    return cases

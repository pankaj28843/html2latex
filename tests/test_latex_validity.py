import os
import shutil
import subprocess
from pathlib import Path

import pytest

from html2latex.api import convert
from html2latex.jinja import render_document
from tests.fixtures.harness import load_fixture_cases

TECTONIC_BIN = shutil.which("tectonic")
RUN_TEX_FIXTURES = os.getenv("HTML2LATEX_TEX_FIXTURES") == "1"


def _build_preamble(packages: set[str]) -> str:
    return "\n".join(f"\\usepackage{{{package}}}" for package in sorted(packages))


def _infer_packages_from_tex(tex: str) -> set[str]:
    packages: set[str] = set()
    if "\\href" in tex or "\\url" in tex:
        packages.add("hyperref")
    if "\\includegraphics" in tex:
        packages.add("graphicx")
    if "\\sout" in tex:
        packages.add("ulem")
    if "\\colorbox" in tex or "\\textcolor" in tex:
        packages.add("xcolor")
    return packages


def _run_tectonic(tex_source: str, tmp_path: Path, name: str) -> None:
    tex_path = tmp_path / f"{name}.tex"
    tex_path.write_text(tex_source)
    command = [TECTONIC_BIN, "--keep-logs", "--outdir", str(tmp_path), str(tex_path)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, (
        f"Tectonic compilation failed.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}\n"
    )


def _ensure_nonempty_body(body: str) -> str:
    tokens = body.strip().split()
    if not tokens or all(token == "\\par" for token in tokens):
        return f"{body}\n\\mbox{{}}" if body.strip() else "\\mbox{}"
    return body


def test_latex_fixtures_compile(tmp_path: Path) -> None:
    if not TECTONIC_BIN:
        pytest.skip("Tectonic not installed; skipping LaTeX validity checks.")
    cases = load_fixture_cases(filters=["blocks/", "inline/", "lists/", "e2e-wysiwyg/"])

    fragments = []
    packages: set[str] = set()
    for case in cases:
        doc = convert(case.html)
        # Use raw tex content (not normalized) for compilation
        tex_content = case.tex.strip()
        if "\\includegraphics" in tex_content or "\\write18" in tex_content:
            continue
        fragments.append(tex_content)
        packages.update(doc.packages)
        packages.update(_infer_packages_from_tex(tex_content))

    body = "\n\n".join(fragments)
    preamble = _build_preamble(packages)
    tex_source = render_document(_ensure_nonempty_body(body), preamble=preamble)
    _run_tectonic(tex_source, tmp_path, "fixtures")


@pytest.mark.parametrize(
    "case",
    load_fixture_cases(filters=["blocks/", "inline/", "lists/", "e2e-wysiwyg/"]),
    ids=lambda case: case.case_id,
)
def test_fixture_tex_files_compile(tmp_path: Path, case) -> None:
    if not TECTONIC_BIN:
        pytest.skip("Tectonic not installed; skipping LaTeX validity checks.")
    if not RUN_TEX_FIXTURES:
        pytest.skip("Set HTML2LATEX_TEX_FIXTURES=1 to validate each fixture individually.")
    # Use raw tex content (not normalized) for compilation
    tex_content = case.tex.strip()
    if "\\includegraphics" in tex_content or "\\write18" in tex_content:
        pytest.skip("Fixture uses external assets or write18.")
    doc = convert(case.html)
    packages = set(doc.packages)
    packages.update(_infer_packages_from_tex(tex_content))
    preamble = _build_preamble(packages)
    tex_source = render_document(_ensure_nonempty_body(tex_content), preamble=preamble)
    safe_id = case.case_id.replace("/", "_")
    _run_tectonic(tex_source, tmp_path, safe_id)

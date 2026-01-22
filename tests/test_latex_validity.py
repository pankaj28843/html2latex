import json
import shutil
import subprocess
from pathlib import Path

import pytest

from html2latex.api import convert
from html2latex.jinja import render_document

TECTONIC_BIN = shutil.which("tectonic")


def _build_preamble(packages: set[str]) -> str:
    return "\n".join(f"\\usepackage{{{package}}}" for package in sorted(packages))


def test_latex_fixtures_compile(tmp_path: Path) -> None:
    if not TECTONIC_BIN:
        pytest.fail("Tectonic is required for LaTeX validity checks; install `tectonic`.")
    cases = []
    for path in sorted(Path("tests/golden").glob("*.json")):
        with path.open() as handle:
            cases.extend(json.load(handle))

    fragments = []
    packages: set[str] = set()
    for case in cases:
        doc = convert(case["html"])
        if "\\includegraphics" in doc.body or "\\write18" in doc.body:
            continue
        fragments.append(doc.body)
        packages.update(doc.packages)

    body = "\n\n".join(fragments)
    preamble = _build_preamble(packages)
    tex_source = render_document(body, preamble=preamble)
    tex_path = tmp_path / "fixtures.tex"
    tex_path.write_text(tex_source)

    command = [TECTONIC_BIN, "--keep-logs", "--outdir", str(tmp_path), str(tex_path)]

    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 0, (
        f"Tectonic compilation failed.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}\n"
    )

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from html2latex.html2latex import html2latex

TECTONIC_BIN = shutil.which("tectonic")


def _build_document(body: str) -> str:
    preamble = """\\documentclass{article}
\\usepackage[table]{xcolor}
\\usepackage[normalem]{ulem}
\\usepackage{hyperref}
\\usepackage{enumitem}
\\usepackage{multirow}
\\usepackage{tabularx}
\\usepackage{array}
\\usepackage{graphicx}
\\begin{document}
"""
    return f"{preamble}\n{body}\n\\end{{document}}\n"


def test_latex_fixtures_compile(tmp_path: Path) -> None:
    if not TECTONIC_BIN:
        pytest.fail("Tectonic is required for LaTeX validity checks; install `tectonic`.")
    cases = []
    for path in sorted(Path("tests/golden").glob("*.json")):
        with path.open() as handle:
            cases.extend(json.load(handle))

    fragments = []
    for case in cases:
        output = html2latex(case["html"])
        if "\\includegraphics" in output or "\\write18" in output:
            continue
        fragments.append(output)

    body = "\n\n".join(fragments)
    tex_source = _build_document(body)
    tex_path = tmp_path / "fixtures.tex"
    tex_path.write_text(tex_source)

    command = [TECTONIC_BIN, "--keep-logs", "--outdir", str(tmp_path), str(tex_path)]

    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 0, (
        f"Tectonic compilation failed.\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}\n"
    )

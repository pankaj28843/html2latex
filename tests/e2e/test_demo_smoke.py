import importlib.util
import os
import time
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

import pytest


def _load_demo_app():
    module_path = Path(__file__).resolve().parents[2] / "demo-app" / "app.py"
    spec = importlib.util.spec_from_file_location("demo_app", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.app


def _start_server(app):
    from werkzeug.serving import make_server

    server = make_server("127.0.0.1", 0, app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _wait_for_server(url: str, timeout: float = 20.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for demo app at {url}")


def test_demo_smoke() -> None:
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    original_env = os.environ.copy()
    os.environ["CACHE_ENABLED"] = "false"
    os.environ["CAPFIRST_ENABLED"] = "false"
    os.environ["ENV"] = "development"

    server = None
    thread = None

    try:
        app = _load_demo_app()
        server, thread = _start_server(app)
        url = f"http://127.0.0.1:{server.server_port}/"
        _wait_for_server(url)

        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch()
            except PlaywrightError as exc:
                if "Executable doesn't exist" in str(exc):
                    pytest.skip("Playwright browsers not installed")
                raise

            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_function("window.tinymce && window.tinymce.activeEditor")
            page.evaluate("() => tinymce.activeEditor.setContent('<p>Smoke Test</p>')")
            page.click("#convert-button")
            page.wait_for_selector("#latex-output code.language-latex")
            output = page.text_content("#latex-output code.language-latex") or ""
            browser.close()

        assert "Smoke Test" in output
        assert "\\noindent" in output
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        if server is not None:
            server.shutdown()
        if thread is not None:
            thread.join(timeout=2)

import tracemalloc

from html2latex.html2latex import html2latex


def test_tracemalloc_snapshot():
    tracemalloc.start()
    html2latex("<p>Hello memory</p>")
    snapshot = tracemalloc.take_snapshot()
    stats = snapshot.statistics("lineno")
    tracemalloc.stop()
    assert stats

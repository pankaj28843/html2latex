# Benchmarks

Run the performance benchmark on the sample corpus:

```bash
uv run python benchmarks/performance.py
```

Run the benchmark against the golden fixture corpus:

```bash
uv run python benchmarks/performance.py --data-dir tests/fixtures/html2latex
```

To compare against a baseline:

```bash
uv run python benchmarks/performance.py --baseline benchmarks/baseline.json
```

Baseline JSON format (threshold is a ratio; 0.2 == 20% regression):

```json
{
  "threshold_ratio": 0.2,
  "cases": {
    "wysiwyg.html": {"mean_ms": 3.2}
  }
}
```

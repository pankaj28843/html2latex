# Benchmarks

Run the performance benchmark on the sample corpus:

```bash
uv run python benchmarks/performance.py
```

To compare against a baseline:

```bash
uv run python benchmarks/performance.py --baseline benchmarks/baseline.json
```

Baseline JSON format:

```json
{
  "threshold_percent": 0.2,
  "cases": {
    "wysiwyg.html": {"mean_ms": 3.2}
  }
}
```

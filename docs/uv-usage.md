# uv Usage

This project uses `uv` for dependency management and reproducible environments.

## Common commands

- Create / sync environment:
  ```bash
  uv sync
  ```

- Run commands in the project env:
  ```bash
  uv run python -m pytest
  ```

- Update lockfile after dependency changes:
  ```bash
  uv lock
  ```

- Add a dependency:
  ```bash
  uv add package-name
  ```

- Export to requirements.txt (if needed):
  ```bash
  uv export --format requirements-txt
  ```

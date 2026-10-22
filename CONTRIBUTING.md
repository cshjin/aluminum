# Contributing

## Development setup

Use Python 3.10 or newer. Install the package and development tools, then run
the same checks used by CI:

```bash
python -m pip install -e ".[dev]"
ruff check src tests
pytest -q
```

Documentation changes can be checked with:

```bash
python -m pip install -e ".[docs]"
mkdocs build
```

## Commit and pull request titles

Use Conventional Commit subjects, for example:

- `fix(detect): honor the configured Ollama port`
- `feat(cli): add a backend option`
- `docs: clarify gateway port precedence`
- `ci: test supported Python versions`

Human-authored pull request titles are checked by CI and must use one of these
types:
`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`,
`chore`, or `revert`. An optional lowercase scope is supported. Dependabot and
Copilot pull requests are exempt because their titles are generated
automatically.

## Pull requests

Keep changes focused, add or update tests for behavior changes, and update
documentation when user-facing behavior changes. Never include API keys,
tokens, certificates, or other secrets in code, logs, or issue reports.

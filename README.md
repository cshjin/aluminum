# ALUMINUM — An LLM Unified Mesh

<p align="center">
  <img src="docs/assets/ALUMINUM_logo.png" alt="ALUMINUM logo" width="480">
</p>

<p align="center">
  <a href="https://github.com/cshjin/aluminum"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="version"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-blue" alt="python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
</p>

One-command aggregator that unifies **Argo**, **ALCF**, **AskSage** and local
**Ollama** behind a single OpenAI-compatible endpoint, using
[`llm-rosetta-gateway`](https://github.com/Oaklight/llm-rosetta) as the
translation mesh (default port **46701**).

ALUMINUM is a **configuration & orchestration layer**: it does not re-implement the
gateway. It detects which upstream services are alive on this machine, lets you
pick services + models in the terminal, generates `config.jsonc` for
`llm-rosetta-gateway`, and launches everything in the right order.

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   Argo   │  │   ALCF   │  │ AskSage  │  │  Ollama  │
│  :8101  │  │  :8102  │  │  :8103  │  │  :8104  │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     └─────────────┴────────────┴────────────┘
                          │
              llm-rosetta-gateway :46701
              (OpenAI + Anthropic compat)
                          │
              your agents / SDKs / Claude Code
```

## Quickstart

```bash
pip install -e ".[all]"        # or: pip install aluminum[all]

aluminum doctor                     # probe local backends + gateway
aluminum setup                      # interactive wizard: pick services, pick models
aluminum serve                      # launch backends (if needed) + gateway on :46701
aluminum status                     # health of mesh + per-provider stats
aluminum models                     # list unified models through the mesh
```

Point any OpenAI-compatible client at the mesh:

```bash
export OPENAI_BASE_URL="http://127.0.0.1:46701/v1"
export OPENAI_API_KEY="dummy"
```

For Claude Code / Anthropic-compatible clients:

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:46701/v1"
export ANTHROPIC_AUTH_TOKEN="dummy"
```

## Docs

Full step-by-step guide: `mkdocs serve` in this repo, or see `docs/`.

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Layout

- `src/aluminum/` — CLI + backend registry + gateway config builder
- `docs/` — mkdocs-material documentation (English-first)
- `tests/` — offline unit tests (no network required)
- `examples/` — sample `config.jsonc` and systemd units

# ALUM — An LLM Unified Mesh

One-command aggregator that unifies **Argo**, **ALCF**, **AskSage** and local
**Ollama** behind a single OpenAI-compatible endpoint, using
[`llm-rosetta-gateway`](https://github.com/Oaklight/llm-rosetta) as the
translation mesh (default port **46701**).

ALUM is a **configuration & orchestration layer**: it does not re-implement the
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
pip install -e ".[all]"        # or: pip install alum[all]

alum doctor                     # probe local backends + gateway
alum setup                      # interactive wizard: pick services, pick models
alum serve                      # launch backends (if needed) + gateway on :46701
alum status                     # health of mesh + per-provider stats
alum models                     # list unified models through the mesh
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

- `src/alum/` — CLI + backend registry + gateway config builder
- `docs/` — mkdocs-material documentation (English-first)
- `tests/` — offline unit tests (no network required)
- `examples/` — sample `config.jsonc` and systemd units

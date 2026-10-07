# Architecture

```
Argo :8101 ─┐
ALCF :8102 ─┼─► llm-rosetta-gateway :46701 ─► agents / SDKs / Claude Code
AskSage :8103┤   (OpenAI + Anthropic compat, llm-rosetta IR)
Ollama :8104┘
```

## Why an orchestration layer?

Each upstream already ships its own proxy (`argo-proxy`, `alcf-proxy`,
`asksage-proxy`, `ollama serve`). What is missing is:

- uniform **discovery** (which services are up? which models exist?),
- uniform **naming** (`argo:…`, `alcf:…`, `asksage:…`, `ollama:…`),
- one **generated config** for the gateway instead of hand-edited JSONC,
- one **CLI** (`alum`) that works the same on every machine.

## Module map

| Module | Responsibility |
|---|---|
| `alum.backends` | backend registry, curated fallbacks, mesh naming |
| `alum.detect` | HTTP probing + live model listing |
| `alum.gateway` | `config.jsonc` builder, writer, launcher |
| `alum.ports` | port resolution (explicit flag > `ALUM_*_PORT` env > placeholder) |
| `alum.config` | shared constants (`mesh_base_url`) |
| `alum.cli` | `doctor / setup / serve / status / models / show` |

## Port conventions

Backend defaults are **placeholders, not real ports** — set yours via
`alum setup` prompts, `--argo-port/--alcf-port/--asksage-port/--ollama-port`
flags, or `ALUM_ARGO_PORT` / `ALUM_ALCF_PORT` / `ALUM_ASKSAGE_PORT` /
`ALUM_OLLAMA_PORT` env vars.

| Service | Placeholder | Env var |
|---|---|---|
| Ollama | 8104 | `ALUM_OLLAMA_PORT` |
| Argo proxy | 8101 | `ALUM_ARGO_PORT` |
| ALCF proxy | 8102 | `ALUM_ALCF_PORT` |
| AskSage proxy | 8103 | `ALUM_ASKSAGE_PORT` |
| **ALUM mesh** | **46701** | `ALUM_PORT` / `--port` |

Bind the mesh to `127.0.0.1` and expose it remotely only via `ssh -L`
(see Operations).

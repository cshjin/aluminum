# Architecture

```
Argo :11444 ─┐
ALCF :11445 ─┼─► llm-rosetta-gateway :46701 ─► agents / SDKs / Claude Code
AskSage :11446┤   (OpenAI + Anthropic compat, llm-rosetta IR)
Ollama :11434┘
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
| `alum.backends` | backend registry, default ports, curated fallbacks, mesh naming |
| `alum.detect` | HTTP probing + live model listing |
| `alum.gateway` | `config.jsonc` builder, writer, launcher |
| `alum.config` | shared constants (`mesh_base_url`) |
| `alum.cli` | `doctor / setup / serve / status / models / show` |

## Port conventions

| Service | Default |
|---|---|
| Ollama | 11434 |
| Argo proxy | 11444 |
| ALCF proxy | 11445 |
| AskSage proxy | 11446 |
| **ALUM mesh** | **46701** |

Bind the mesh to `127.0.0.1` and expose it remotely only via `ssh -L`
(see Operations).

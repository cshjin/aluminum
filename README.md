# ALUMINUM — An LLM Unified Mesh

<p align="center">
  <img src="docs/assets/ALUMINUM_logo.png" alt="ALUMINUM logo" width="480">
</p>

<p align="center">
  <a href="https://github.com/cshjin/aluminum"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="version"></a>
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

## Optional LiteLLM gateway

The existing Rosetta gateway remains the default. To use
[LiteLLM Proxy](https://docs.litellm.ai/docs/proxy/quick_start) instead:

```bash
pip install -e ".[litellm]"           # installed package: pip install "aluminum[litellm]"
export LITELLM_MASTER_KEY="sk-$(openssl rand -hex 32)"  # keep this secret across restarts
aluminum setup --gateway litellm
aluminum serve --gateway litellm
aluminum doctor --gateway litellm
aluminum status --gateway litellm
aluminum models --gateway litellm
aluminum costs                      # configured rates, including unknown prices
aluminum costs --json                # machine-readable USD/token rates
```

Setup writes `litellm.yaml` in the platform's ALUMINUM user config directory
(Linux: `~/.config/aluminum/litellm.yaml`), separate from Rosetta's config.
Use `--config /path/to/config.yaml` on setup, serve, show, and costs to override it.
Pass the same `--host` and `--port` to serve as setup; LiteLLM's YAML does not
store the listening address. `aluminum models` and OpenAI clients use the same
`http://127.0.0.1:46701/v1` endpoint with either gateway. For LiteLLM, set
`OPENAI_API_KEY` to your gateway key (not `dummy`). CLI gateway probes and model
listing use `ALUM_GATEWAY_API_KEY` if set, otherwise `LITELLM_MASTER_KEY`.
For production, issue restricted virtual keys rather than distributing the
master key; LiteLLM virtual-key/budget persistence requires its database setup.

For a remote gateway behind a TLS-terminating reverse proxy, use HTTPS explicitly:

```bash
aluminum models --gateway litellm --host gateway.example --port 443 --scheme https
aluminum status --gateway litellm --host gateway.example --port 443 --scheme https
```

`--host` accepts a hostname or IP address, not a URL. Authenticated requests to
non-loopback HTTP addresses are refused before any network request; local
loopback HTTP remains supported. Both model and health probes use the selected
scheme. HTTPS verifies certificates using the system trust configuration (or
HTTPX's `SSL_CERT_FILE` / `SSL_CERT_DIR` for your organization's CA); there is no
insecure TLS bypass or automatic fallback to HTTP.

Argo, ALCF, AskSage, and Ollama retain their exact upstream model IDs and route
through their existing local OpenAI-compatible proxies. Start those proxies
separately; ALUMINUM does not replace provider authentication or certificates.
You can also edit `model_list` in the generated YAML to add
[native LiteLLM providers](https://docs.litellm.ai/docs/providers).
Keep credentials in environment variables, referencing them as
`api_key: os.environ/PROVIDER_API_KEY`, rather than writing secrets into YAML.
The LiteLLM gateway binds to loopback by default and reads its master key from
`LITELLM_MASTER_KEY`; generated YAML contains only the environment reference.
Keep this variable set in the serve process. Before binding
to any non-loopback host, configure `general_settings.master_key` using an
environment reference and set that variable; ALUMINUM refuses an unprotected
non-loopback launch. Use authenticated clients and TLS for remote access.

### Pricing

Rates are USD **per single token** (`$15 / 1M tokens` = `0.000015`). By default no
prices are guessed from model names: missing prices are **unknown**, not zero.
Apply the built-in defaults, or supply your own verified rates:

```bash
aluminum setup --gateway litellm --default-pricing        # new config
aluminum costs --apply-defaults                            # existing config (writes a .bak)
aluminum setup --gateway litellm --pricing rates.yaml      # your own rates
aluminum costs                                             # compare rates per 1M tokens
```

`--default-pricing` fills only models without explicit rates:

| Provider | Default rate |
| --- | --- |
| ALCF, AskSage, Ollama | $0 (treated as free) |
| Argo | [GitHub Copilot's published USD per-token rates](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing), default (non-long-context) tier, including cache read/write |
| anything else | unknown |

Custom rates go in a YAML file mapping mesh model names to rates. Input and output
are required; cache rates are optional for models that bill cached tokens:

```yaml
argo:claude-opus-5:                      # $5 in / $25 out / $0.50 cache read / $6.25 cache write per 1M
  input_cost_per_token: 0.000005
  output_cost_per_token: 0.000025
  cache_read_input_token_cost: 0.0000005
  cache_creation_input_token_cost: 0.00000625
alcf:gpt-oss-120b:                       # explicitly free
  input_cost_per_token: 0
  output_cost_per_token: 0
```

Rates must be finite, non-negative numbers and become LiteLLM's custom
`litellm_params` cost values. `aluminum costs` only compares configured rates per
million tokens; it makes no API calls and reports neither invoices nor actual
usage. For hand-edited native-provider configs it also reads explicit rates in
`model_info`; conflicting explicit rates are rejected. Without explicit rates,
LiteLLM may estimate public prices that are not verified for your institutional
proxy.

Choose a cheaper suitable model explicitly using its mesh name. For equivalent
deployments, LiteLLM also supports
[cost-based routing](https://docs.litellm.ai/docs/routing#cost-based-routing);
enable it only after verifying prices and model equivalence. ALUMINUM does not
automatically route requests to unknown-price providers or claim billing savings.

### Usage per model

Usage needs the LiteLLM database (set `DATABASE_URL`, e.g. a local Postgres) and the
gateway key (`LITELLM_MASTER_KEY` or `ALUM_GATEWAY_API_KEY`) in your environment:

```bash
aluminum usage                 # all recorded requests
aluminum usage --days 7        # last 7 days
aluminum usage --json          # machine-readable
```

It lists, per model: requests, failures, input / output / cache read / cache write
tokens, total tokens in millions, and USD spend computed from the configured rates
(unpriced models show $0). Rows appear about a minute after the request.

### OpenTelemetry (opt-in)

```bash
pip install -e ".[otel]"             # installed package: pip install "aluminum[otel]"
export OTEL_SERVICE_NAME=aluminum-mesh
export LITELLM_MASTER_KEY="sk-$(openssl rand -hex 32)"  # or reuse your existing secret
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
aluminum setup --gateway litellm --otel
aluminum serve --gateway litellm
```

Run an OTLP collector separately (for example, one forwarding to Jaeger or
Grafana). Setup enables LiteLLM's native `otel` callback; no collector or database
is bundled. Request traces can expose latency, errors, model/provider identity,
and usage/cost when available from the upstream and LiteLLM. Missing token usage
or institutional pricing cannot be reconstructed reliably and must not be
interpreted as zero. `status` only reports availability; use your observability
backend for request statistics.

Generated configs disable prompt/response message logging with
`turn_off_message_logging: true`, including when tracing is enabled. Telemetry
is off unless `--otel` is selected. Trace metadata can still be sensitive: use a
trusted collector, configure exporter authentication via environment variables,
and review retention/access controls. See
[LiteLLM OpenTelemetry](https://docs.litellm.ai/docs/observability/opentelemetry_integration)
for exporter configuration and available attributes.

## Docs

Full step-by-step guide: `mkdocs serve` in this repo, or see `docs/`.

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development checks and commit
guidelines. Pull requests run lint, tests across supported Python versions,
package build, and documentation build.

## Layout

- `src/aluminum/` — CLI + backend registry + gateway config builder
- `docs/` — mkdocs-material documentation (English-first)
- `tests/` — offline unit tests (no network required)
- `examples/` — sample `config.jsonc` and systemd units

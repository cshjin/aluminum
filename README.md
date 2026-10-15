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

## Optional LiteLLM gateway

The existing Rosetta gateway remains the default. To use
[LiteLLM Proxy](https://docs.litellm.ai/docs/proxy/quick_start) instead:

```bash
pip install -e ".[litellm]"           # installed package: pip install "aluminum[litellm]"
aluminum setup --gateway litellm
aluminum serve --gateway litellm
aluminum doctor --gateway litellm
aluminum status --gateway litellm
aluminum costs                      # configured rates, including unknown prices
aluminum costs --json                # machine-readable USD/token rates
```

Setup writes `litellm.yaml` in the platform's ALUMINUM user config directory
(Linux: `~/.config/aluminum/litellm.yaml`), separate from Rosetta's config.
Use `--config /path/to/config.yaml` on setup, serve, show, and costs to override it.
Pass the same `--host` and `--port` to serve as setup; LiteLLM's YAML does not
store the listening address. `aluminum models` and OpenAI clients use the same
`http://127.0.0.1:46701/v1` endpoint with either gateway.

Argo, ALCF, AskSage, and Ollama retain their exact upstream model IDs and route
through their existing local OpenAI-compatible proxies. Start those proxies
separately; ALUMINUM does not replace provider authentication or certificates.
You can also edit `model_list` in the generated YAML to add
[native LiteLLM providers](https://docs.litellm.ai/docs/providers).
Keep credentials in environment variables, referencing them as
`api_key: os.environ/PROVIDER_API_KEY`, rather than writing secrets into YAML.
The gateway binds to loopback by default without authentication. Before binding
to any non-loopback host, configure `general_settings.master_key` using an
environment reference and set that variable; ALUMINUM refuses an unprotected
non-loopback launch. Use authenticated clients and TLS for remote access.

### Pricing and incomplete provider information

No prices or capabilities are guessed from model names. Missing prices are
**unknown**, not zero; even local models have infrastructure costs and Ollama
cloud billing may differ. Supply verified rates with
`aluminum setup --gateway litellm --pricing /path/to/rates.yaml`, for example:

```yaml
# Illustrative rates only: replace with your provider's verified USD/token rates.
alcf:gpt-oss-120b:
  input_cost_per_token: 0.000001
  output_cost_per_token: 0.000002
```

Both rates must be finite, non-negative numbers. Only explicitly verified free
token rates should be zero. These rates become LiteLLM's custom
`litellm_params.input_cost_per_token` / `output_cost_per_token` values.
`aluminum costs` compares configured rates per million tokens; it does not make
API calls, estimate missing usage, report actual invoices, or include cache,
image, subscription, or infrastructure charges. For hand-edited native-provider
configs it likewise reports only explicit custom rates, not LiteLLM's built-in
public price catalogue. LiteLLM may otherwise estimate public model prices;
those estimates are not verified prices for your institutional proxy.

Choose a cheaper suitable model explicitly using its mesh name. For equivalent
deployments, LiteLLM also supports
[cost-based routing](https://docs.litellm.ai/docs/routing#cost-based-routing);
enable it only after verifying prices and model equivalence. ALUMINUM does not
automatically route requests to unknown-price providers or claim billing savings.

### OpenTelemetry (opt-in)

```bash
pip install -e ".[otel]"             # installed package: pip install "aluminum[otel]"
export OTEL_SERVICE_NAME=aluminum-mesh
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

## Layout

- `src/aluminum/` — CLI + backend registry + gateway config builder
- `docs/` — mkdocs-material documentation (English-first)
- `tests/` — offline unit tests (no network required)
- `examples/` — sample `config.jsonc` and systemd units

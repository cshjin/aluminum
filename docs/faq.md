# FAQ

**Is ALUM a fork of llm-rosetta-gateway?**
No. ALUM generates its config and launches it. Protocol translation stays
entirely in `llm-rosetta`.

**Why port 46701?**
It is just the default. Override it with `alum setup` (Step 1), `--port`,
or the `ALUM_PORT` env var.

**Can I use ALUM on a machine with only some backends?**
Yes — that is the point. `alum doctor` shows what is reachable; `alum setup`
only offers reachable services (plus curated fallbacks you can deselect).

**Where are secrets stored?**
Nowhere in ALUM. API keys and certs live in each proxy's own config
(`argo-proxy`, `alcf-proxy`, `asksage-proxy`, `ollama`). The generated
`config.jsonc` only contains `dummy` placeholders and routing.

**How do I add a backend?**
See Backends → "Adding a new backend". It is a ~10-line change in
`src/alum/backends.py`.

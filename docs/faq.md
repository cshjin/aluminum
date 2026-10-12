# FAQ

**Is ALUMINUM a fork of llm-rosetta-gateway?**
No. ALUMINUM generates its config and launches it. Protocol translation stays
entirely in `llm-rosetta`.

**Why port 46701?**
It is just the default. Override it with `aluminum setup` (Step 1), `--port`,
or the `ALUM_PORT` env var.

**Can I use ALUMINUM on a machine with only some backends?**
Yes — that is the point. `aluminum doctor` shows what is reachable; `aluminum setup`
only offers reachable services (plus curated fallbacks you can deselect).

**Where are secrets stored?**
Nowhere in ALUMINUM. API keys and certs live in each proxy's own config
(`argo-proxy`, `alcf-proxy`, `asksage-proxy`, `ollama`). The generated
`config.jsonc` only contains `dummy` placeholders and routing.

**How do I add a backend?**
See Backends → "Adding a new backend". It is a ~10-line change in
`src/aluminum/backends.py`.

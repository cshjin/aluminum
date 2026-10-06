# Quickstart

## 1. Install

```bash
pip install -e ".[all]"
```

For docs tooling:

```bash
pip install -e ".[docs]"
mkdocs serve
```

## 2. Check the machine

```bash
alum doctor
```

Expected: one row per backend (`argo`, `alcf`, `asksage`, `ollama`) plus the
mesh gateway on `127.0.0.1:46701`. Missing rows simply mean that proxy is not
running — the wizard will only offer what it can reach (plus curated
fallbacks).

## 3. Run the wizard

```bash
alum setup
```

Four steps:

1. **Port** — mesh gateway port (default `46701`); warns if occupied.
2. **Pick services** — checkbox-style numbered list; nothing pre-selected.
2. **Pick models per service** — fetched live from each `/v1/models`
   (Ollama via `/api/tags`); curated fallbacks apply when a backend is down.
3. **Confirm** — writes `~/.config/llm-rosetta-gateway/config.jsonc`
   (previous file is backed up to `.jsonc.bak`).

Non-interactive equivalent (CI / containers):

```bash
alum setup --yes
```

## 4. Serve the mesh

```bash
alum serve
```

Then point any client at the mesh:

```bash
export OPENAI_BASE_URL="http://127.0.0.1:46701/v1"
export OPENAI_API_KEY="dummy"
```

## 5. Verify

```bash
alum status
alum models
curl http://127.0.0.1:46701/v1/models
```

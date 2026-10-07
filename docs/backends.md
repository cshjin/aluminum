# Backends

Setup discovers models **local-first**, so every offered id is routable
through the local proxy. Fallback order per backend:

| Backend | 1st: local proxy | 2nd fallback | 3rd: curated |
|---|---|---|---|
| Argo | `:8101/v1/models` | prod `https://apps.inside.anl.gov/argoapi/v1/models` (public, no auth) | ✅ |
| ALCF | `:8102/v1/models` | `alcf-proxy models --json` (owns Globus auth; see [inference-endpoints docs](https://docs.alcf.anl.gov/services/inference-endpoints)) | ✅ |
| AskSage | `:8103/v1/models` | cached `~/.config/asksage_proxy/available_models.json` ([API docs](https://docs.asksage.ai/api-documentation/)) | ✅ |
| Ollama | `:8104/api/tags` | auto-start `ollama serve` if down, then re-check | ✅ |

!!! warning "Argo prod vs local ids differ"

    The prod catalogue uses display-style ids (`Claude Opus 5`) while the
    local dev proxy serves routable ids (`argo:claude-opus-5`) — zero overlap
    (37 vs 57 entries, verified 2026-10-06). The wizard therefore lists the
    **local** proxy first; the prod URL is only a fallback when the proxy is
    down. If you switch `argo-proxy` to the prod environment, re-run
    `alum setup` to pick up the new ids.

## Argo (`argo-proxy`)

- Single gateway provider block `argo` (`openai_chat` → `/v1`). argo-proxy
  natively serves both `/v1/chat/completions` and `/v1/messages`, so one
  block covers GPT- and Claude-flavoured models; the mesh translates the
  other protocol on the fly (verified live for both directions).
- Mesh names keep the `argo:` prefix.
- Serve hint: `argo-proxy serve`. Config lives at
  `~/.config/argoproxy/config.yaml`.

## ALCF (`alcf-proxy`)

- Single `openai_chat` provider block pointed at `/v1`.
- Model list comes from the cluster scheduler (Sophia/Metis/Minerva, vLLM).
- Serve hint: `alcf-proxy serve`.

## AskSage (`asksage-proxy`)

- Single `openai_chat` provider block (`AskSage`).
- Requires a personal API key and the ANL cert (`asksage_anl_gov.pem`).
  Never commit keys — the wizard never writes secrets, only `dummy` placeholders
  plus model routing (auth lives in each proxy's own config).
- Serve hint: `asksage-proxy`. Config at `~/.config/asksage_proxy/config.yaml`.

## Ollama

- Local daemon; also serves Ollama **cloud** models (`*:cloud`) after
  `ollama signin`. Cloud entries appear with size `-` in `ollama list`.
- Model discovery uses `/api/tags` (different schema from `/v1/models`);
  ALUM normalises both to a plain id list.
- Serve hint: `ollama serve`.

## Adding a new backend

1. Add an entry to `REGISTRY` in `src/alum/backends.py`
   (key, label, port, gateway provider block, models URL).
2. Add curated fallbacks in `CURATED_MODELS`.
3. Extend `mesh_name()` prefix mapping.
4. Document the service in this page.

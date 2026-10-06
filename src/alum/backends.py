"""Backend registry: one entry per upstream service.

Each backend knows:
- its default local port,
- how to build gateway provider block(s),
- how to fetch its upstream model list for the setup wizard.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Backend:
    key: str
    label: str
    default_port: int
    gateway_providers: dict
    models_url: str = ""
    description: str = ""
    # CLI entry that serves this backend (informational only).
    serve_hint: str = ""
    # Direct upstream model catalogue (no local proxy needed).
    # Argo: prod endpoint is public (no auth); note its IDs are display-style
    # ("Claude Opus 5") and differ from the local dev proxy's routable IDs
    # ("argo:claude-opus-5"), so the local proxy stays the primary source.
    upstream_models_url: str = ""
    # Path (under platformdirs user_config_dir) to a cached model catalogue.
    cache_file: str = ""


def _providers_for(base_url: str, kind: str = "openai_chat") -> dict:
    return {"type": kind, "base_url": base_url, "api_key": "dummy"}


REGISTRY: dict[str, Backend] = {
    "argo": Backend(
        key="argo",
        label="Argo (ANL gateway)",
        default_port=11444,
        gateway_providers={
            "argo": {
                "type": "openai_chat",
                "base_url": "http://127.0.0.1:11444/v1",
                "api_key": "dummy",
            }
        },
        models_url="http://127.0.0.1:11444/v1/models",
        description="ANL Argo gateway; all models over OpenAI chat "
        "(argo-proxy also speaks Anthropic natively, the mesh translates).",
        serve_hint="argo-proxy serve",
        upstream_models_url="https://apps.inside.anl.gov/argoapi/v1/models",
    ),
    "alcf": Backend(
        key="alcf",
        label="ALCF / Sophia cluster",
        default_port=11445,
        gateway_providers={"alcf": _providers_for("http://127.0.0.1:11445/v1")},
        models_url="http://127.0.0.1:11445/v1/models",
        description="ALCF open models (Sophia/Metis/Minerva, vLLM).",
        serve_hint="alcf-proxy serve",
    ),
    "asksage": Backend(
        key="asksage",
        label="AskSage",
        default_port=11446,
        gateway_providers={"AskSage": _providers_for("http://127.0.0.1:11446/v1")},
        models_url="http://127.0.0.1:11446/v1/models",
        description="AskSage proxy (needs API key + ANL cert).",
        serve_hint="asksage-proxy",
        cache_file="asksage_proxy/available_models.json",
    ),
    "ollama": Backend(
        key="ollama",
        label="Local Ollama (incl. cloud models)",
        default_port=11434,
        gateway_providers={"ollama": _providers_for("http://127.0.0.1:11434/v1")},
        models_url="http://127.0.0.1:11434/api/tags",
        description="Local Ollama daemon; cloud models need `ollama signin`.",
        serve_hint="ollama serve",
    ),
}

GATEWAY_DEFAULT_HOST = "127.0.0.1"
GATEWAY_DEFAULT_PORT = 46701  # ANL founded 1 July 1946

# Curated fallback models per provider (used when live discovery fails).
CURATED_MODELS: dict[str, list[str]] = {
    "argo": [
        "argo:claude-opus-5",
        "argo:claude-sonnet-5",
        "argo:gpt-5.6-sol",
        "argo:gpt-5.6-terra",
        "argo:gpt-5.6-luna",
    ],
    "alcf": ["inkling-bf16", "nemotron-3-ultra", "gpt-oss-120b"],
    "asksage": ["google-claude-sonnet-5", "gpt-5.6-luna", "gpt-6-luna"],
    "ollama": ["gpt-oss:120b-cloud", "nemotron-3-ultra:cloud", "qwen3:8b"],
}

DEFAULT_CAPABILITIES = ["text", "tools", "vision", "reasoning"]


def mesh_name(provider_key: str, upstream_model: str) -> str:
    """Map an upstream model id to its mesh-level name.

    Convention: ``<prefix>:<short>`` where prefix groups by backend
    (``argo:``, ``alcf:``, ``asksage:``, ``ollama:``).
    """
    prefix = {
        "argo": "argo",
        "alcf": "alcf",
        "asksage": "asksage",
        "ollama": "ollama",
    }[provider_key]
    short = upstream_model.replace("argo:", "").replace("/", "-").replace(":", "-")
    return f"{prefix}:{short}"

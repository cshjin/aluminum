"""Backend registry: one entry per upstream service.

No machine-specific ports live here — see ``alum.ports``. Each backend
declares *templates* (``{port}`` placeholder); concrete URLs are built at
runtime from resolved ports so generated configs match the user's machine.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Backend:
    key: str
    label: str
    # Gateway provider block template: (provider_name, provider_type, base_path).
    # base_path is appended to ``http://127.0.0.1:{port}``.
    provider_name: str
    provider_type: str
    base_path: str
    # Local proxy endpoints (port filled in at runtime).
    models_path: str = "/v1/models"
    description: str = ""
    # CLI entry that serves this backend (informational only).
    serve_hint: str = ""
    # Direct upstream model catalogue (no local proxy needed).
    upstream_models_url: str = ""
    # Path (under platformdirs user_config_dir) to a cached model catalogue.
    cache_file: str = ""

    def base_url(self, port: int) -> str:
        return f"http://127.0.0.1:{port}{self.base_path}"

    def models_url(self, port: int) -> str:
        return f"http://127.0.0.1:{port}{self.models_path}"

    def provider_block(self, port: int) -> dict:
        return {
            self.provider_name: {
                "type": self.provider_type,
                "base_url": self.base_url(port),
                "api_key": "dummy",
            }
        }


REGISTRY: dict[str, Backend] = {
    "argo": Backend(
        key="argo",
        label="Argo (ANL gateway)",
        provider_name="argo",
        provider_type="openai_chat",
        base_path="/v1",
        description="ANL Argo gateway; all models over OpenAI chat "
        "(argo-proxy also speaks Anthropic natively, the mesh translates).",
        serve_hint="argo-proxy serve",
        upstream_models_url="https://apps.inside.anl.gov/argoapi/v1/models",
    ),
    "alcf": Backend(
        key="alcf",
        label="ALCF / Sophia cluster",
        provider_name="alcf",
        provider_type="openai_chat",
        base_path="/v1",
        description="ALCF open models (Sophia/Metis/Minerva, vLLM).",
        serve_hint="alcf-proxy serve",
    ),
    "asksage": Backend(
        key="asksage",
        label="AskSage",
        provider_name="AskSage",
        provider_type="openai_chat",
        base_path="/v1",
        description="AskSage proxy (needs API key + ANL cert).",
        serve_hint="asksage-proxy",
        cache_file="asksage_proxy/available_models.json",
    ),
    "ollama": Backend(
        key="ollama",
        label="Local Ollama (incl. cloud models)",
        provider_name="ollama",
        provider_type="openai_chat",
        base_path="/v1",
        models_path="/api/tags",
        description="Local Ollama daemon; cloud models need `ollama signin`.",
        serve_hint="ollama serve",
    ),
}

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

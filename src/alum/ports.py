"""Central port registry.

No machine-specific ports live here: backend defaults are neutral
placeholders. Resolve order for every key:
explicit argument > ``ALUM_*_PORT`` env var > placeholder default.
Set the env vars (or answer the setup prompts) to match your proxies.
"""

from __future__ import annotations

import os

GATEWAY_DEFAULT_PORT = 46701

DEFAULTS: dict[str, int] = {
    "gateway": GATEWAY_DEFAULT_PORT,
    "argo": 8101,
    "alcf": 8102,
    "asksage": 8103,
    "ollama": 8104,
}

ENV_VARS: dict[str, str] = {
    "gateway": "ALUM_PORT",
    "argo": "ALUM_ARGO_PORT",
    "alcf": "ALUM_ALCF_PORT",
    "asksage": "ALUM_ASKSAGE_PORT",
    "ollama": "ALUM_OLLAMA_PORT",
}


def resolve(key: str, explicit: int | None = None) -> int:
    """Resolve the port for ``key`` (``gateway``/``argo``/``alcf``/``asksage``/``ollama``)."""
    if explicit is not None:
        return explicit
    env_name = ENV_VARS[key]
    raw = os.environ.get(env_name, "").strip()
    if raw.isdigit() and 1 <= int(raw) <= 65535:
        return int(raw)
    return DEFAULTS[key]


def resolve_all(explicit: dict[str, int | None] | None = None) -> dict[str, int]:
    """Resolve every backend port; ``explicit`` maps key -> port (None = unset)."""
    explicit = explicit or {}
    return {k: resolve(k, explicit.get(k)) for k in ("argo", "alcf", "asksage", "ollama")}

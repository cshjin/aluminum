"""Probing helpers: is a backend alive? which models does it expose?"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import time
from pathlib import Path

import httpx
from platformdirs import user_config_dir

from alum.backends import REGISTRY

TIMEOUT = 5.0


def probe_port(port: int, path: str = "/v1/models", timeout: float = TIMEOUT) -> tuple[bool, str]:
    """Return (alive, detail) for a local HTTP endpoint."""
    from alum.config import mesh_base_url

    url = mesh_base_url(port=port) + path if port == 46701 else f"http://127.0.0.1:{port}{path}"
    try:
        r = httpx.get(url, timeout=timeout)
        if r.status_code < 500:
            return True, f"HTTP {r.status_code}"
        return False, f"HTTP {r.status_code}"
    except Exception as e:  # noqa: BLE001 — report anything as down
        return False, f"{type(e).__name__}: {e}"


def probe_backend(key: str, timeout: float = TIMEOUT) -> dict:
    backend = REGISTRY[key]
    if key == "ollama":
        alive, detail = probe_port(backend.default_port, path="/api/tags", timeout=timeout)
    else:
        alive, detail = probe_port(backend.default_port, path="/v1/models", timeout=timeout)
    return {"key": key, "label": backend.label, "alive": alive, "detail": detail}


def probe_all(timeout: float = TIMEOUT) -> list[dict]:
    return [probe_backend(k, timeout=timeout) for k in REGISTRY]


def probe_gateway(host: str = "127.0.0.1", port: int = 46701, timeout: float = TIMEOUT) -> dict:
    alive, detail = probe_port(port, path="/v1/models", timeout=timeout)
    health = {}
    if alive:
        try:
            r = httpx.get(f"http://{host}:{port}/health", timeout=timeout)
            if r.status_code == 200:
                health = r.json()
        except Exception:  # noqa: BLE001 — health is best-effort
            health = {}
    return {"alive": alive, "detail": detail, "health": health}


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """True if something already listens on host:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def parse_port(raw: str, default: int) -> int | None:
    """Validate a port string; return None when invalid."""
    raw = raw.strip()
    if not raw:
        return default
    if raw.isdigit() and 1 <= int(raw) <= 65535:
        return int(raw)
    return None


# ---------------------------------------------------------------------------
# Model discovery — one chain per backend, local-first so every offered
# model id is guaranteed routable through the local proxy.
# ---------------------------------------------------------------------------


def _ids_from_openai_models(data: dict) -> list[str]:
    if isinstance(data.get("data"), list):
        return sorted(m["id"] for m in data["data"] if isinstance(m, dict) and m.get("id"))
    return []


def _ids_from_ollama_tags(data: dict) -> list[str]:
    if isinstance(data.get("models"), list):
        out = []
        for m in data["models"]:
            if isinstance(m, dict):
                out.append(m.get("name") or m.get("model") or "")
            elif isinstance(m, str):
                out.append(m)
        return sorted(x for x in out if x)
    return []


def _fetch_json(url: str, timeout: float) -> dict | None:
    try:
        r = httpx.get(url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001 — fall through to next source
        return None


def _alcf_models_via_cli(timeout: float = 60.0) -> list[str]:
    """Ask alcf-proxy itself (it owns Globus auth + cluster routing).

    Output lines look like ``sophia/vllm: <model>``; strip the cluster prefix
    since alcf-proxy serve already routes by model id.
    """
    exe = shutil.which("alcf-proxy")
    if not exe:
        return []
    try:
        proc = subprocess.run(
            [exe, "models", "--json"], capture_output=True, text=True, timeout=timeout, check=False
        )
    except Exception:  # noqa: BLE001 — fall through to next source
        return []
    if proc.returncode != 0:
        return []
    try:
        data = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return []
    names = data if isinstance(data, list) else []
    out = []
    for entry in names:
        if isinstance(entry, str) and ":" in entry:
            out.append(entry.split(":", 1)[1].strip())
        elif isinstance(entry, str):
            out.append(entry.strip())
    return sorted(x for x in out if x)


def _asksage_models_via_cache() -> list[str]:
    backend = REGISTRY["asksage"]
    if not backend.cache_file:
        return []
    path = Path(user_config_dir()) / backend.cache_file
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return []
    chat = data.get("chat_models", {}) if isinstance(data, dict) else {}
    return sorted(chat) if isinstance(chat, dict) else []


def ensure_ollama(timeout: float = 30.0) -> bool:
    """Make sure the local Ollama daemon is up, starting it if needed."""
    alive, _ = probe_port(REGISTRY["ollama"].default_port, path="/api/tags", timeout=TIMEOUT)
    if alive:
        return True
    exe = shutil.which("ollama")
    if not exe:
        return False
    log = Path("/tmp") / "alum-ollama-serve.log"
    with log.open("ab") as fh:
        subprocess.Popen(
            [exe, "serve"], stdout=fh, stderr=subprocess.STDOUT, start_new_session=True
        )
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(1.0)
        alive, _ = probe_port(REGISTRY["ollama"].default_port, path="/api/tags", timeout=TIMEOUT)
        if alive:
            return True
    return False


def fetch_upstream_models(key: str, timeout: float = 15.0) -> list[str]:
    """Best-effort model ids for the wizard (local-first, then fallbacks)."""
    from alum.backends import CURATED_MODELS

    backend = REGISTRY[key]
    sources: list[list[str]] = []

    if key == "ollama":
        data = _fetch_json(backend.models_url, timeout) or {}
        sources.append(_ids_from_ollama_tags(data))
    elif key == "alcf":
        data = _fetch_json(backend.models_url, timeout) or {}
        sources.append(_ids_from_openai_models(data))
        if not sources[-1]:
            sources.append(_alcf_models_via_cli())
    elif key == "asksage":
        data = _fetch_json(backend.models_url, timeout) or {}
        sources.append(_ids_from_openai_models(data))
        if not sources[-1]:
            sources.append(_asksage_models_via_cache())
    else:  # argo and future plain OpenAI-compat backends
        data = _fetch_json(backend.models_url, timeout) or {}
        sources.append(_ids_from_openai_models(data))
        if not sources[-1] and backend.upstream_models_url:
            upstream = _fetch_json(backend.upstream_models_url, timeout=20.0) or {}
            sources.append(_ids_from_openai_models(upstream))

    for ids in sources:
        if ids:
            return ids
    return list(CURATED_MODELS.get(key, []))

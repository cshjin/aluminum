"""Shared constants for ALUM."""

from alum.ports import GATEWAY_DEFAULT_PORT


def mesh_base_url(host: str = "127.0.0.1", port: int = GATEWAY_DEFAULT_PORT) -> str:
    return f"http://{host}:{port}"

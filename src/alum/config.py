"""Shared constants for ALUM."""

from alum.backends import GATEWAY_DEFAULT_HOST, GATEWAY_DEFAULT_PORT


def mesh_base_url(host: str = GATEWAY_DEFAULT_HOST, port: int = GATEWAY_DEFAULT_PORT) -> str:
    return f"http://{host}:{port}"

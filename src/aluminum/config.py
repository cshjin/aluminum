"""Shared constants for ALUMINUM."""

from ipaddress import ip_address

import httpx

from aluminum.ports import GATEWAY_DEFAULT_PORT


def mesh_base_url(
    host: str = "127.0.0.1", port: int = GATEWAY_DEFAULT_PORT, scheme: str = "http",
) -> str:
    if scheme not in {"http", "https"}:
        raise ValueError("Gateway scheme must be http or https")
    if not host or any(c in host for c in "/\\@?#%") or any(c.isspace() for c in host):
        raise ValueError("Gateway host must be a hostname or IP address, not a URL")
    return str(httpx.URL(scheme=scheme, host=host.removeprefix("[").removesuffix("]"), port=port))


def gateway_request_url(
    host: str, port: int, scheme: str = "http", headers: dict[str, str] | None = None,
) -> str:
    """Require TLS before sending credentials beyond literal loopback addresses."""
    url = mesh_base_url(host, port, scheme)
    hostname = httpx.URL(url).host
    try:
        loopback = ip_address(hostname).is_loopback
    except ValueError:
        loopback = hostname == "localhost"
    if headers and scheme == "http" and not loopback:
        raise ValueError("Refusing to send gateway credentials over non-loopback HTTP; use --scheme https")
    return url

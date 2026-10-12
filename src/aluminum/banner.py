"""Startup banner for ALUMINUM (ANSI block style, like argo-proxy / llm-rosetta-gateway)."""

from __future__ import annotations

import os
import sys

_A = [
    " █████╗ ",
    "██╔══██╗",
    "███████║",
    "██╔══██║",
    "██║  ██║",
    "╚═╝  ╚═╝",
]

_L = [
    "██╗     ",
    "██║     ",
    "██║     ",
    "██║     ",
    "███████╗",
    "╚══════╝",
]

_U = [
    "██╗   ██╗",
    "██║   ██║",
    "██║   ██║",
    "██║   ██║",
    "╚██████╔╝",
    " ╚═════╝ ",
]

_M = [
    "███╗   ███╗",
    "████╗ ████║",
    "██╔████╔██║",
    "██║╚██╔╝██║",
    "██║ ╚═╝ ██║",
    "╚═╝     ╚═╝",
]

_I = [
    "██╗",
    "██║",
    "██║",
    "██║",
    "██║",
    "╚═╝",
]

_N = [
    "███╗   ██╗",
    "████╗  ██║",
    "██╔██╗ ██║",
    "██║╚██╗██║",
    "██║ ╚████║",
    "╚═╝  ╚═══╝",
]

_LETTERS = [_A, _L, _U, _M, _I, _N, _U, _M]

# One color per letter (repeated letters share a color):
# A cyan / L green / U yellow / M magenta / I blue / N red.
COLORS = [
    "bright_cyan",
    "bright_green",
    "bright_yellow",
    "bright_magenta",
    "bright_blue",
    "bright_red",
    "bright_yellow",
    "bright_magenta",
]

SEP = " "

BANNER = "\n" + "\n".join(SEP.join(letter[i] for letter in _LETTERS) for i in range(6)) + "\n"


def _colored() -> str:
    import click

    rows = []
    for i in range(6):
        rows.append(
            SEP.join(click.style(letter[i], fg=color) for letter, color in zip(_LETTERS, COLORS))
        )
    return "\n" + "\n".join(rows) + "\n"


def print_banner() -> None:
    """Print the startup banner with version info."""
    from aluminum import __version__
    from aluminum.ports import GATEWAY_DEFAULT_PORT

    use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    print(_colored() if use_color else BANNER)
    print(f"  ALUMINUM — An LLM Unified Mesh  v{__version__}")
    print(f"  mesh default: http://127.0.0.1:{GATEWAY_DEFAULT_PORT}/v1")
    print()

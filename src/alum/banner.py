"""Startup banner for ALUM (ANSI block style, like argo-proxy / llm-rosetta-gateway)."""

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

_LETTERS = [_A, _L, _U, _M]

# One color per letter: cyan / green / amber / magenta (bright variants pop on dark terminals).
COLORS = ["bright_cyan", "bright_green", "bright_yellow", "bright_magenta"]

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
    from alum import __version__

    use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    print(_colored() if use_color else BANNER)
    print(f"  ALUM — An LLM Unified Mesh  v{__version__}")
    print("  mesh default: http://127.0.0.1:46701/v1")
    print()

"""Opt-in default USD prices: free ALCF/AskSage/Ollama, Argo at GitHub Copilot's published rates."""

from __future__ import annotations

FREE_PROVIDERS = frozenset({"alcf", "asksage", "ollama"})
PRICED_PROVIDERS = frozenset({"argo"})

# USD per 1M tokens at the default (non-long-context) tier:
# (input, cached input, cache write or None, output).
# Source: https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing
COPILOT_USD_PER_M: dict[str, tuple[float, float, float | None, float]] = {
    "claude-haiku-4.5": (1.00, 0.10, 1.25, 5.00),
    "claude-haiku-5.5": (0.10, 0.01, 0.125, 0.50),
    "claude-sonnet-4": (3.00, 0.30, 3.75, 15.00),
    "claude-sonnet-4.6": (3.00, 0.30, 3.75, 15.00),
    "claude-sonnet-5": (2.00, 0.20, 2.50, 10.00),
    "claude-sonnet-5.5": (2.00, 0.10, 2.50, 10.00),
    "claude-opus-4.8": (5.00, 0.50, 6.25, 25.00),
    "claude-opus-5": (5.00, 0.50, 6.25, 25.00),
    "claude-opus-5.5": (4.00, 0.20, 5.00, 20.00),
    "claude-fable-5": (10.00, 1.00, 12.50, 50.00),
    "claude-fable-5.1": (10.00, 0.25, 12.50, 50.00),
    "gpt-5-mini": (0.25, 0.025, None, 2.00),
    "gpt-5.3-codex": (1.75, 0.175, None, 14.00),
    "gpt-5.4": (2.50, 0.25, None, 15.00),
    "gpt-5.4-mini": (0.75, 0.075, None, 4.50),
    "gpt-5.4-nano": (0.20, 0.02, None, 1.25),
    "gpt-5.5": (5.00, 0.50, None, 30.00),
    "gpt-5.6-luna": (0.20, 0.02, 0.25, 1.20),
    "gpt-5.6-sol": (4.00, 0.40, 5.00, 20.00),
    "gpt-5.6-terra": (2.00, 0.20, 2.50, 12.00),
    "gpt-6-astra": (10.00, 1.00, 12.50, 50.00),
    "gpt-6-luna": (0.10, 0.01, 0.125, 0.50),
    "gpt-6-sol": (2.00, 0.20, 2.50, 10.00),
    "gpt-6.1-sol": (2.00, 0.10, 2.50, 10.00),
    "gemini-3.7-flash": (0.75, 0.075, None, 3.75),
    "gemini-3.8-flash": (0.75, 0.075, None, 3.75),
    "gemini-4-argon": (2.00, 0.10, None, 10.00),
    "mai-code-1.1-flash": (0.20, 0.02, None, 1.20),
    "grok-4.5": (2.00, 0.50, None, 6.00),
    "grok-4.6": (2.00, 0.50, None, 6.00),
    "grok-4.7": (2.00, 0.50, None, 6.00),
    "kimi-k3": (3.00, 0.30, None, 15.00),
}


def default_rates(alias: str) -> dict[str, float] | None:
    """USD/token rates for a mesh model name, or None when unknown."""
    provider, _, name = alias.partition(":")
    if provider in FREE_PROVIDERS:
        return {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0}
    if provider in PRICED_PROVIDERS and name.lower() in COPILOT_USD_PER_M:
        inp, cached, write, out = COPILOT_USD_PER_M[name.lower()]
        rates = {
            "input_cost_per_token": inp / 1e6,
            "output_cost_per_token": out / 1e6,
            "cache_read_input_token_cost": cached / 1e6,
        }
        if write is not None:
            rates["cache_creation_input_token_cost"] = write / 1e6
        return rates
    return None

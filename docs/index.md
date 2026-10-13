# ALUMINUM — An LLM Unified Mesh

<p align="center">
  <img src="assets/ALUMINUM_logo.png" alt="ALUMINUM logo" width="480">
</p>

<p align="center">
  <a href="https://github.com/cshjin/aluminum"><img src="https://img.shields.io/badge/version-0.1.0-blue" alt="version"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-blue" alt="python"></a>
  <a href="https://github.com/cshjin/aluminum/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
</p>

ALUMINUM aggregates **Argo**, **ALCF**, **AskSage**, and local **Ollama**
(including Ollama cloud models) behind one OpenAI-compatible endpoint.

The translation mesh is [`llm-rosetta-gateway`](https://github.com/Oaklight/llm-rosetta),
served by default on port **46701**.

ALUMINUM itself is a **configuration & orchestration layer**:

- detects which upstream services are alive,
- walks you through service + model selection in the terminal,
- generates `config.jsonc` for `llm-rosetta-gateway`,
- launches and monitors the whole mesh.

No gateway logic is re-implemented here. If you only need protocol
translation, use `llm-rosetta(-gateway)` directly; if you need one-command
multi-service aggregation with docs, use ALUMINUM.

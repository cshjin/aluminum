"""`alum` command line interface."""

from __future__ import annotations

import json
import sys

import click
import httpx
from rich.console import Console
from rich.table import Table

from alum import __version__
from alum.backends import CURATED_MODELS, GATEWAY_DEFAULT_PORT, REGISTRY, mesh_name
from alum.banner import print_banner
from alum.config import mesh_base_url
from alum.detect import (
    ensure_ollama,
    fetch_upstream_models,
    port_in_use,
    probe_all,
    probe_gateway,
)
from alum.gateway import (
    build_config,
    config_path,
    default_models_for,
    launch_gateway,
    write_config,
)

console = Console()

KEY_HINT = "↑↓ navigate • space toggle • enter submit"

# Arrow-key checkbox UI (InquirerPy) when available + attached to a TTY,
# otherwise fall back to numbered input so pipes/CI keep working.
try:
    from InquirerPy import inquirer as _inquirer
except ImportError:  # pragma: no cover
    _inquirer = None


def _interactive() -> bool:
    return _inquirer is not None and sys.stdin.isatty()


@click.group()
@click.version_option(__version__, prog_name="alum")
def cli() -> None:
    """ALUM — An LLM Unified Mesh (one-command LLM aggregator)."""


@cli.command()
@click.option("--timeout", default=5.0, help="Probe timeout in seconds.")
def doctor(timeout: float) -> None:
    """Probe local backends and the mesh gateway."""
    table = Table(title="ALUM doctor")
    table.add_column("backend")
    table.add_column("endpoint")
    table.add_column("status")
    table.add_column("detail")
    for row in probe_all(timeout=timeout):
        backend = REGISTRY[row["key"]]
        table.add_row(
            row["label"],
            f"127.0.0.1:{backend.default_port}",
            "✅ up" if row["alive"] else "❌ down",
            row["detail"],
        )
    gw = probe_gateway(timeout=timeout)
    table.add_row(
        "mesh gateway",
        f"127.0.0.1:{GATEWAY_DEFAULT_PORT}",
        "✅ up" if gw["alive"] else "❌ down",
        gw["detail"],
    )
    console.print(table)
    if not gw["alive"]:
        console.print("[dim]Hint: run `alum setup` then `alum serve`.[/dim]")


def _multiselect(prompt_text: str, choices: list[str], defaults: list[str]) -> list[str]:
    if _interactive():
        try:
            picked = _inquirer.checkbox(
                message=prompt_text,
                choices=[{"name": c, "value": c, "enabled": c in defaults} for c in choices],
                instruction=KEY_HINT,
            ).execute()
        except KeyboardInterrupt:
            console.print("\nAborted — nothing written.")
            sys.exit(130)
        return picked or [c for c in choices if c in defaults]
    console.print(f"\n[bold]{prompt_text}[/bold]")
    for i, c in enumerate(choices, 1):
        mark = " [default]" if c in defaults else ""
        console.print(f"  {i}. {c}{mark}")
    empty_label = "defaults" if defaults else "none"
    raw = click.prompt(
        f"Enter numbers separated by comma (empty = {empty_label})",
        default="",
        show_default=False,
    ).strip()
    if not raw:
        return [c for c in choices if c in defaults]
    picked = []
    for tok in raw.split(","):
        tok = tok.strip()
        if tok.isdigit() and 1 <= int(tok) <= len(choices):
            picked.append(choices[int(tok) - 1])
    return picked or [c for c in choices if c in defaults]


def _pick_port(cli_port: int | None, yes: bool, default: int = GATEWAY_DEFAULT_PORT) -> int:
    """Step 0 of setup: choose the mesh gateway port."""
    if cli_port is not None:
        if not 1 <= cli_port <= 65535:
            console.print(f"[red]Invalid port {cli_port}: must be 1-65535.[/red]")
            sys.exit(2)
        return cli_port
    if yes:
        return default
    while True:
        port = click.prompt("Mesh gateway port", default=default, type=click.IntRange(1, 65535))
        if port_in_use(port):
            console.print(f"[yellow]Port {port} is already in use.[/yellow]")
            if _confirm(f"Use port {port} anyway?", default=False):
                return int(port)
            continue
        return int(port)


def _confirm(prompt_text: str, default: bool = True) -> bool:
    if _interactive():
        try:
            return bool(_inquirer.confirm(message=prompt_text, default=default).execute())
        except KeyboardInterrupt:
            console.print("\nAborted — nothing written.")
            sys.exit(130)
    return bool(click.confirm(prompt_text, default=default))


def _pick_models(provider_key: str, limit: int = 40) -> dict[str, str]:
    upstream = fetch_upstream_models(provider_key)
    if provider_key == "ollama":
        # Ollama cloud tags are verbose; keep the list manageable.
        upstream = upstream[:limit]
    else:
        upstream = upstream[:limit] or list(CURATED_MODELS.get(provider_key, []))
    choices = upstream or list(CURATED_MODELS.get(provider_key, []))
    # No pre-selection: the user explicitly ticks what they want.
    picked = _multiselect(f"Models for {provider_key}", choices, [])
    out: dict[str, str] = {}
    for up in picked:
        out[mesh_name(provider_key, up)] = up
    return out


@cli.command()
@click.option(
    "--config", "-c", default=None, help="Gateway config path (default: auto-discovered)."
)
@click.option("--host", default="127.0.0.1", help="Gateway bind host.")
@click.option("--port", default=None, type=int, help="Gateway bind port.")
@click.option(
    "--yes", "-y", is_flag=True, help="Non-interactive: use live backends + curated models."
)
@click.option("--no-banner", is_flag=True, help="Suppress the startup banner.")
def setup(config: str | None, host: str, port: int | None, yes: bool, no_banner: bool) -> None:
    """Interactive wizard: choose services, choose models, write gateway config."""
    if not no_banner:
        print_banner()
    console.print("[bold]Step 1/4 — mesh gateway port[/bold]")
    port = _pick_port(port, yes)
    alive = {r["key"]: r["alive"] for r in probe_all()}
    backend_keys = list(REGISTRY)

    if yes:
        provider_keys = [k for k in backend_keys if alive.get(k)] or list(backend_keys)
        models = default_models_for(provider_keys)
    else:
        console.print("\n[bold]Step 2/4 — pick services to join the mesh[/bold]")
        for k in backend_keys:
            flag = "✅ up" if alive.get(k) else "❌ down"
            console.print(f"  • {k}: {REGISTRY[k].label} ({flag}) — {REGISTRY[k].description}")
        # No pre-selection: submit empty to abort.
        provider_keys = _multiselect("Which services join the mesh?", backend_keys, [])
        if not provider_keys:
            console.print("No services selected — aborted, nothing written.")
            return
        if "ollama" in provider_keys and not alive.get("ollama"):
            console.print("Ollama selected but not serving — starting `ollama serve` …")
            if ensure_ollama():
                console.print("✅ Ollama is up.")
                alive["ollama"] = True
            else:
                console.print(
                    "[yellow]Could not start Ollama; its models come from fallback.[/yellow]"
                )
        console.print("\n[bold]Step 3/4 — pick models per service[/bold]")
        models: dict[str, str] = {}
        kept: list[str] = []
        for key in provider_keys:
            picked = _pick_models(key)
            if not picked:
                console.print(f"[dim]Skipped {key}: no models selected.[/dim]")
                continue
            models.update(picked)
            kept.append(key)
        provider_keys = kept
        if not models:
            console.print("No models selected — aborted, nothing written.")
            return
        console.print("\n[bold]Step 4/4 — confirm[/bold]")
        console.print(f"Providers: {', '.join(provider_keys)}")
        console.print(f"Models ({len(models)}): {', '.join(sorted(models))}")
        if not _confirm("Write gateway config?", default=True):
            console.print("Aborted — nothing written.")
            return

    cfg = build_config(provider_keys, models, host=host, port=port)
    path = config_path(config)
    write_config(cfg, path)
    console.print(f"\n✅ Wrote gateway config to [bold]{path}[/bold]")
    console.print(f"   Providers: {', '.join(provider_keys)}  |  Models: {len(models)}")
    console.print(f"   Next: [bold]alum serve[/bold]  (serves on {mesh_base_url(host, port)}/v1)")


@cli.command()
@click.option("--config", "-c", default=None)
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=GATEWAY_DEFAULT_PORT)
@click.option("--no-banner", is_flag=True, help="Suppress the startup banner.")
def serve(config: str | None, host: str, port: int, no_banner: bool) -> None:
    """Launch llm-rosetta-gateway with the alum-generated config."""
    if not no_banner:
        print_banner()
    path = config_path(config)
    if not path.exists():
        console.print(f"[red]No config at {path}. Run `alum setup` first.[/red]")
        sys.exit(1)
    console.print(f"Starting mesh gateway on {mesh_base_url(host, port)} (config: {path}) …")
    console.print("[dim]Make sure upstream proxies are running (argo/alcf/asksage/ollama).[/dim]")
    proc = launch_gateway(path, host=host, port=port)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=GATEWAY_DEFAULT_PORT)
def status(host: str, port: int) -> None:
    """Show mesh health + per-provider stats."""
    gw = probe_gateway(host=host, port=port)
    if not gw["alive"]:
        console.print(f"[red]Gateway down at {mesh_base_url(host, port)} ({gw['detail']})[/red]")
        sys.exit(1)
    health = gw.get("health", {}) or {}
    console.print(
        f"✅ Mesh up — uptime {health.get('uptime_seconds', '?')}s, "
        f"requests {health.get('requests_total', '?')}, "
        f"errors(last h) {health.get('errors_last_hour', '?')}"
    )
    providers = health.get("providers", {}) or {}
    if providers:
        table = Table(title="providers")
        table.add_column("provider")
        table.add_column("status")
        table.add_column("success")
        table.add_column("avg ms")
        for name, st in providers.items():
            table.add_row(
                name,
                str(st.get("status")),
                str(st.get("success_rate")),
                str(st.get("avg_latency_ms")),
            )
        console.print(table)


@cli.command("models")
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=GATEWAY_DEFAULT_PORT)
@click.option("--json", "as_json", is_flag=True, help="Print raw JSON.")
def list_models(host: str, port: int, as_json: bool) -> None:
    """List unified models served through the mesh."""
    url = mesh_base_url(host, port) + "/v1/models"
    try:
        r = httpx.get(url, timeout=10.0)
        r.raise_for_status()
        data = r.json()
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Failed to reach {url}: {e}[/red]")
        sys.exit(1)
    if as_json:
        click.echo(json.dumps(data, indent=2))
        return
    items = data.get("data", []) if isinstance(data, dict) else []
    table = Table(title=f"mesh models ({len(items)})")
    table.add_column("model")
    table.add_column("owner")
    for m in sorted(items, key=lambda x: x.get("id", "")):
        table.add_row(str(m.get("id")), str(m.get("owned_by")))
    console.print(table)


@cli.command()
@click.option("--config", "-c", default=None)
def show(config: str | None) -> None:
    """Print the current gateway config."""
    path = config_path(config)
    if not path.exists():
        console.print(f"[red]No config at {path}. Run `alum setup` first.[/red]")
        sys.exit(1)
    click.echo(path.read_text())


@cli.command()
def version() -> None:
    """Print version."""
    click.echo(__version__)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()

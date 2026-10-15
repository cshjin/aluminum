"""Offline LiteLLM config, pricing, and CLI regression tests."""

import json
from unittest.mock import Mock

import pytest
import yaml
from click.testing import CliRunner

from aluminum import cli, detect
from aluminum import litellm_gateway as gateway
from aluminum.backends import REGISTRY, mesh_name
from aluminum.gateway import default_models_for


def test_all_providers_keep_exact_upstream_ids(monkeypatch):
    monkeypatch.setenv("ALUM_ARGO_PORT", "9101")
    models = {mesh_name(key, "org/model:tag"): "org/model:tag" for key in REGISTRY}
    config = gateway.build_config(list(REGISTRY), models, backend_ports={"ollama": 9104})
    assert len(config["model_list"]) == 4
    for entry in config["model_list"]:
        provider = entry["model_name"].split(":")[0]
        params = entry["litellm_params"]
        assert params["model"] == "openai/org/model:tag"
        assert params["api_base"].endswith("/v1")
        if provider == "argo":
            assert ":9101/" in params["api_base"]
        if provider == "ollama":
            assert ":9104/" in params["api_base"]
    assert config["litellm_settings"] == {"turn_off_message_logging": True}
    assert config["general_settings"]["master_key"] == "os.environ/LITELLM_MASTER_KEY"


def test_prices_are_explicit_and_otel_is_opt_in():
    prices = {"input_cost_per_token": 0, "output_cost_per_token": 0.000002}
    config = gateway.build_config(
        ["argo", "ollama"], {"argo:x": "x", "ollama:y": "y"},
        pricing={"argo:x": prices}, otel=True,
    )
    assert config["litellm_settings"]["callbacks"] == ["otel"]
    assert config["litellm_settings"]["turn_off_message_logging"] is True
    assert config["model_list"][0]["litellm_params"]["input_cost_per_token"] == 0
    rows = gateway.cost_rows(config)
    assert rows[0]["pricing"] == "configured"
    assert rows[1]["pricing"] == "unknown"
    assert rows[1]["input_cost_per_token"] is None
    assert "input_cost_per_token" not in config["model_list"][1]["litellm_params"]


def test_native_model_info_pricing_and_conflicts():
    config = {"model_list": [{
        "model_name": "native", "litellm_params": {"model": "openai/native"},
        "model_info": {"input_cost_per_token": 0.000001, "output_cost_per_token": 0.000002},
    }]}
    assert gateway.cost_rows(config)[0]["input_cost_per_token"] == 0.000001
    config["model_list"][0]["litellm_params"]["input_cost_per_token"] = 0
    with pytest.raises(ValueError, match="Conflicting"):
        gateway.cost_rows(config)


@pytest.mark.parametrize("value", [-1, float("inf"), float("nan"), True, "1", None])
def test_invalid_prices_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        gateway.validate_prices({"input_cost_per_token": value, "output_cost_per_token": 0})


@pytest.mark.parametrize("pricing", [
    {"ollama:x": {"input_cost_per_token": 0}},
    {"other:x": {"input_cost_per_token": 0, "output_cost_per_token": 0}},
    [],
])
def test_incomplete_or_unselected_pricing_rejected(pricing):
    with pytest.raises(ValueError):
        gateway.build_config(["ollama"], {"ollama:x": "x"}, pricing=pricing)


@pytest.mark.parametrize("providers,models", [
    ([], {}), (["missing"], {"missing:x": "x"}),
    (["argo"], {"ollama:x": "x"}), (["argo"], {"x": "x"}), (["argo"], {}),
])
def test_invalid_routes_rejected(providers, models):
    with pytest.raises(ValueError):
        gateway.build_config(providers, models)


def test_yaml_roundtrip_backup_and_default_path(tmp_path, monkeypatch):
    monkeypatch.setattr(gateway, "user_config_dir", lambda _: str(tmp_path))
    path = gateway.config_path()
    assert path == tmp_path / "litellm.yaml"
    config = gateway.build_config(["asksage"], default_models_for(["asksage"]))
    gateway.write_config(config, path)
    original = path.read_text()
    gateway.write_config(config, path)
    assert yaml.safe_load(path.read_text()) == config
    assert path.with_suffix(".yaml.bak").read_text() == original


def test_launch_uses_explicit_local_bind_and_config(tmp_path, monkeypatch):
    monkeypatch.setattr(gateway.shutil, "which", lambda _: "/bin/litellm")
    popen = Mock()
    monkeypatch.setattr(gateway.subprocess, "Popen", popen)
    path = tmp_path / "config with spaces.yaml"
    gateway.launch_gateway(path, port=9999)
    popen.assert_called_once_with([
        "/bin/litellm", "--config", str(path), "--host", "127.0.0.1", "--port", "9999",
    ])


def test_launch_missing_runtime_is_actionable(tmp_path, monkeypatch):
    monkeypatch.setattr(gateway.shutil, "which", lambda _: None)
    with pytest.raises(ValueError, match=r"aluminum\[litellm\]"):
        gateway.launch_gateway(tmp_path / "config.yaml")


def test_nonlocal_bind_requires_resolved_master_key(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text("general_settings:\n  master_key: os.environ/ALUM_TEST_MASTER_KEY\n")
    monkeypatch.delenv("ALUM_TEST_MASTER_KEY", raising=False)
    with pytest.raises(ValueError, match="master_key"):
        gateway.launch_gateway(path, host="0.0.0.0")
    monkeypatch.setenv("ALUM_TEST_MASTER_KEY", "test-only-not-a-real-credential")
    monkeypatch.setattr(gateway.shutil, "which", lambda _: "/bin/litellm")
    popen = Mock()
    monkeypatch.setattr(gateway.subprocess, "Popen", popen)
    gateway.launch_gateway(path, host="0.0.0.0")
    assert popen.called


def test_cli_setup_show_costs_and_serve(tmp_path, monkeypatch):
    runner = CliRunner()
    path = tmp_path / "gateway.yaml"
    monkeypatch.setattr(cli, "probe_all", lambda **_: [{"key": "argo", "alive": True}])
    result = runner.invoke(cli.cli, [
        "setup", "--gateway", "litellm", "--yes", "--no-banner", "--otel",
        "--config", str(path), "--argo-port", "9111", "--port", "9999",
    ])
    assert result.exit_code == 0, result.output
    assert "--port 9999" in result.output
    config = yaml.safe_load(path.read_text())
    assert config["model_list"][0]["litellm_params"]["api_base"] == "http://127.0.0.1:9111/v1"
    result = runner.invoke(cli.cli, ["show", "--gateway", "litellm", "-c", str(path)])
    assert result.exit_code == 0
    assert "model_list" in result.output
    result = runner.invoke(cli.cli, ["costs", "-c", str(path), "--json"])
    assert result.exit_code == 0
    assert all(row["pricing"] == "unknown" for row in json.loads(result.output))
    proc = Mock(returncode=7)
    launch = Mock(return_value=proc)
    monkeypatch.setattr(gateway, "launch_gateway", launch)
    result = runner.invoke(cli.cli, [
        "serve", "--gateway", "litellm", "--no-banner", "-c", str(path), "--port", "9999",
    ])
    assert result.exit_code == 7
    launch.assert_called_once_with(path, host="127.0.0.1", port=9999)


def test_cli_pricing_file_and_invalid_input(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "probe_all", lambda **_: [{"key": "ollama", "alive": True}])
    path = tmp_path / "gateway.yaml"
    rates = tmp_path / "rates.yaml"
    alias = next(iter(default_models_for(["ollama"])))
    rates.write_text(yaml.safe_dump({
        alias: {"input_cost_per_token": 0, "output_cost_per_token": 0},
    }))
    args = [
        "setup", "--gateway", "litellm", "-y", "--no-banner",
        "-c", str(path), "--pricing", str(rates),
    ]
    result = CliRunner().invoke(cli.cli, args)
    assert result.exit_code == 0, result.output
    assert gateway.cost_rows(yaml.safe_load(path.read_text()))[0]["pricing"] == "configured"
    original = path.read_text()
    rates.write_text("not-a-mapping")
    result = CliRunner().invoke(cli.cli, args)
    assert result.exit_code == 1
    assert path.read_text() == original


@pytest.mark.parametrize("text", ["invalid", "model_list: [null]", "model_list: ["])
def test_cli_bad_cost_config_is_readable_error(tmp_path, text):
    path = tmp_path / "bad.yaml"
    path.write_text(text)
    result = CliRunner().invoke(cli.cli, ["costs", "-c", str(path)])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_otel_rejected_for_rosetta():
    result = CliRunner().invoke(cli.cli, ["setup", "--otel", "--no-banner"])
    assert result.exit_code == 2
    assert "--gateway litellm" in result.output


def test_rosetta_remains_default(tmp_path, monkeypatch):
    path = tmp_path / "config.jsonc"
    monkeypatch.setattr(cli, "probe_all", lambda **_: [{"key": "argo", "alive": True}])
    result = CliRunner().invoke(cli.cli, ["setup", "-y", "--no-banner", "-c", str(path)])
    assert result.exit_code == 0
    assert '"providers"' in path.read_text()
    assert "model_list" not in path.read_text()


def test_litellm_health_does_not_trigger_upstream_requests(monkeypatch):
    get = Mock(return_value=Mock(status_code=200, json=lambda: {"status": "alive"}))
    monkeypatch.setattr(detect.httpx, "get", get)
    result = detect.probe_gateway(gateway="litellm", port=9999)
    assert result["alive"] is True
    urls = [call.args[0] for call in get.call_args_list]
    assert urls == ["http://127.0.0.1:9999/v1/models", "http://127.0.0.1:9999/health/liveliness"]


def test_gateway_credentials_are_not_sent_to_backends(monkeypatch):
    monkeypatch.setenv("LITELLM_MASTER_KEY", "test-only-master")
    monkeypatch.setenv("ALUM_GATEWAY_API_KEY", "test-only-virtual")
    get = Mock(return_value=Mock(status_code=200, json=dict))
    monkeypatch.setattr(detect.httpx, "get", get)
    detect.probe_gateway(gateway="litellm")
    for call in get.call_args_list:
        assert call.kwargs["headers"] == {"Authorization": "Bearer " + "test-only-virtual"}
    get.reset_mock()
    detect.probe_backend("argo")
    assert "headers" not in get.call_args.kwargs
    monkeypatch.delenv("ALUM_GATEWAY_API_KEY")
    assert gateway.request_headers() == {"Authorization": "Bearer " + "test-only-master"}


@pytest.mark.parametrize("status_code", [401, 403, 404, 500])
def test_litellm_probe_rejects_http_errors(monkeypatch, status_code):
    get = Mock(return_value=Mock(status_code=status_code))
    monkeypatch.setattr(detect.httpx, "get", get)
    assert detect.probe_gateway(gateway="litellm")["alive"] is False
    assert get.call_count == 1


def test_cli_models_authentication(monkeypatch):
    monkeypatch.setenv("ALUM_GATEWAY_API_KEY", "test-only-virtual")
    get = Mock(return_value=Mock(json=lambda: {"data": []}))
    monkeypatch.setattr(cli.httpx, "get", get)
    result = CliRunner().invoke(cli.cli, ["models", "--gateway", "litellm", "--json"])
    assert result.exit_code == 0
    assert get.call_args.kwargs["headers"] == {"Authorization": "Bearer " + "test-only-virtual"}

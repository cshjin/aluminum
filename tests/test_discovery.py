"""Offline tests for model discovery chains (httpx/subprocess mocked)."""

import json

import httpx

from alum import detect
from alum.detect import fetch_upstream_models, parse_port, port_in_use


def test_parse_port():
    assert parse_port("", 46701) == 46701
    assert parse_port("  ", 46701) == 46701
    assert parse_port("8080", 46701) == 8080
    assert parse_port("0", 46701) is None
    assert parse_port("99999", 46701) is None
    assert parse_port("abc", 46701) is None


def test_port_in_use_detects_live_gateway():
    assert port_in_use(46701) is True
    assert port_in_use(9) is False  # discard port, almost surely closed


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_argo_prefers_local_proxy_ids(monkeypatch):
    """Local proxy IDs must win: prod display-style IDs are not routable."""
    calls = []

    def fake_get(url, timeout=None):
        calls.append(url)
        if "127.0.0.1" in url:
            return _Resp({"data": [{"id": "argo:claude-opus-5"}]})
        return _Resp({"data": [{"id": "Claude Opus 5"}]})

    monkeypatch.setattr(httpx, "get", fake_get)
    assert fetch_upstream_models("argo") == ["argo:claude-opus-5"]
    assert not any("apps.inside" in c for c in calls)


def test_argo_falls_back_to_prod_url(monkeypatch):
    def fake_get(url, timeout=None):
        if "127.0.0.1" in url:
            raise httpx.ConnectError("down")
        return _Resp({"data": [{"id": "Claude Opus 5"}]})

    monkeypatch.setattr(httpx, "get", fake_get)
    assert fetch_upstream_models("argo") == ["Claude Opus 5"]


def test_alcf_cli_output_strips_cluster_prefix(monkeypatch, tmp_path):
    import subprocess

    monkeypatch.setattr(detect.shutil, "which", lambda _: "/usr/bin/alcf-proxy")
    payload = ["sophia/vllm: gpt-oss-120b", "minerva/api: inkling-bf16"]

    class _Proc:
        returncode = 0
        stdout = json.dumps(payload)

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Proc())

    def fake_get(url, timeout=None):
        raise httpx.ConnectError("proxy down")

    monkeypatch.setattr(httpx, "get", fake_get)
    assert fetch_upstream_models("alcf") == ["gpt-oss-120b", "inkling-bf16"]


def test_asksage_cache_fallback(monkeypatch, tmp_path):
    cache_dir = tmp_path / "asksage_proxy"
    cache_dir.mkdir()
    (cache_dir / "available_models.json").write_text(
        json.dumps({"chat_models": {"gpt-5.6-luna": {}, "zzz-model": {}}})
    )
    monkeypatch.setattr(detect, "user_config_dir", lambda *a, **k: str(tmp_path))

    def fake_get(url, timeout=None):
        raise httpx.ConnectError("proxy down")

    monkeypatch.setattr(httpx, "get", fake_get)
    assert fetch_upstream_models("asksage") == ["gpt-5.6-luna", "zzz-model"]


def test_curated_last_resort(monkeypatch):
    def fake_get(url, timeout=None):
        raise httpx.ConnectError("all down")

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(detect.shutil, "which", lambda _: None)
    got = fetch_upstream_models("asksage")
    assert "gpt-5.6-luna" in got  # curated fallback

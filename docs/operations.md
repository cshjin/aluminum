# Operations

## Remote access via SSH tunnel

Bind everything to `127.0.0.1`. Never expose an unauthenticated proxy on
`0.0.0.0`. From your laptop:

```bash
ssh -N -L 46701:127.0.0.1:46701 user@server
curl http://localhost:46701/v1/models
```

For flaky networks use `autossh -M 0 -N -L …`.

## Persistence

Simplest (interactive hosts):

```bash
tmux new -s alum
alum serve
# Ctrl+B, D to detach
```

Stable (servers), as a user systemd unit `~/.config/systemd/user/alum.service`:

```ini
[Unit]
Description=ALUM mesh gateway
After=network.target

[Service]
ExecStart=%h/.local/bin/alum serve
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable --now alum
```

## Client wiring

OpenAI-compatible tools (Aider, Cursor, Python SDK):

```bash
export OPENAI_BASE_URL="http://localhost:46701/v1"
export OPENAI_API_KEY="dummy"
```

Claude Code:

```bash
export ANTHROPIC_BASE_URL="http://localhost:46701/v1"
export ANTHROPIC_AUTH_TOKEN="dummy"
```

## Troubleshooting

- **Gateway up, model errors** — check `alum status` provider table; the
  failing upstream (Argo/ALCF/AskSage/Ollama) is usually down or its key/cert
  expired.
- **AskSage SSL errors** — verify `cert_path` in
  `~/.config/asksage_proxy/config.yaml` points at a valid `asksage_anl_gov.pem`.
- **Ollama cloud models missing** — run `ollama signin`, then `ollama list`.

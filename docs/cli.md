# CLI Reference

```
alum --help
alum doctor [--timeout 5.0]
alum setup [-c CONFIG] [--host 127.0.0.1] [--port 46701] [--yes]
alum serve [-c CONFIG] [--host 127.0.0.1] [--port 46701]
alum status [--host 127.0.0.1] [--port 46701]
alum models [--host 127.0.0.1] [--port 46701] [--json]
alum show [-c CONFIG]
alum version
```

## doctor

Probe every registered backend plus the mesh gateway. Exit code is always 0;
read the ✅/❌ table.

## setup

Interactive wizard (three steps: services → models → confirm). Service and
model steps use arrow-key checkboxes: **↑↓** to move, **space** to
toggle, **enter** to submit. Nothing is pre-selected — submit empty to abort.
The final step asks for confirmation before overwriting. Writes
`~/.config/llm-rosetta-gateway/config.jsonc` with a `.jsonc.bak` backup.
`--yes` skips prompts using live backends + curated models. When stdin is
not a TTY (pipes, CI), selection falls back to numbered input.

## serve

Execs `llm-rosetta-gateway --config <path> [--host …] [--port …]` in the
foreground. Run it under `tmux`, `screen`, or systemd for persistence
(see Operations). Upstream proxies must already be running.

## status / models

`status` prints gateway uptime, request counters and per-provider success
rate / latency (from `/health`). `models` lists the unified model catalogue
(from `/v1/models`); `--json` dumps raw JSON for scripting.

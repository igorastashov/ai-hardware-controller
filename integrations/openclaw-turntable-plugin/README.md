# OpenClaw Turntable External Plugin

External plugin package for OpenClaw that maps `turntable_*` tools to `ai-hardware-controller` HTTP API.

## Build and test

```bash
cd integrations/openclaw-turntable-plugin
npm install
npm run test
npm run build
npm run smoke
```

## Operator config examples

```bash
openclaw config set plugins.entries.turntable.enabled true
openclaw config set plugins.load.paths '["/abs/path/to/integrations/openclaw-turntable-plugin"]'
openclaw config set plugins.entries.turntable.config.baseUrl "http://192.168.31.97:8000"
openclaw config set plugins.entries.turntable.config.allowSideEffects true
openclaw config set agents.list[0].tools.allow '["turntable_state","turntable_move_to","turntable_stop"]'
```

## Safety defaults

- Side-effect tools are disabled by default (`allowSideEffects=false`).
- Motion requires pre-state check (`status == IDLE`).
- Anti-flood and idempotency guard are enabled by default.
- Ambiguous move failure path attempts `turntable_stop`.

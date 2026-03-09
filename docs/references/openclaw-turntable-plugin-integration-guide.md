# OpenClaw Turntable Plugin Integration Guide

## Scope
Подключение внешнего plugin без модификации OpenClaw core.

## Install options

### Option A: local plugin install
```bash
openclaw plugins install -l /abs/path/to/integrations/openclaw-turntable-plugin
```

### Option B: config-based load paths
```bash
openclaw config set plugins.load.paths '["/abs/path/to/integrations/openclaw-turntable-plugin"]'
```

## Enable plugin
```bash
openclaw config set plugins.entries.turntable.enabled true
```

## Configure plugin runtime
```bash
openclaw config set plugins.entries.turntable.config.baseUrl "http://192.168.31.97:8000"
openclaw config set plugins.entries.turntable.config.timeoutMs 30000
openclaw config set plugins.entries.turntable.config.retry.maxAttempts 2
openclaw config set plugins.entries.turntable.config.retry.backoffMs 400
openclaw config set plugins.entries.turntable.config.allowSideEffects true
openclaw config set plugins.entries.turntable.config.commandGapMs 250
openclaw config set plugins.entries.turntable.config.idempotencyWindowMs 1500
```

## Agent allowlist policy
Включайте только нужные tools конкретному агенту:

```bash
openclaw config set agents.list[0].id "main"
openclaw config set agents.list[0].tools.allow '[
  "turntable_state",
  "turntable_home",
  "turntable_move_to",
  "turntable_return_base",
  "turntable_stop",
  "turntable_commissioning_first_run"
]'
```

Если видите ошибку `agents.list.0.id: expected string`, значит агент еще не инициализирован.
Сначала задайте `agents.list[0].id`, затем повторите allowlist команду.

## Rollback
1. Disable plugin:
   - `openclaw config set plugins.entries.turntable.enabled false`
2. Remove turntable tools from agent allowlist.
3. Continue with host-only API/CLI runbook until issue is resolved.

## Known runtime note (OpenClaw 2026.3.8)

В текущем окружении наблюдался кейс: plugin `turntable` в статусе `loaded`, но `turntable_*` не попадают в фактический toolset агента (`Tool turntable_state not found`).

Проверка перед эскалацией:
- `openclaw plugins info turntable`
- `openclaw config get agents.list[0].tools`
- `openclaw gateway restart`

Если проблема сохраняется, работайте по fallback-процедуре из `docs/references/openclaw-turntable-operator-workflow.md` (HTTP API/CLI + агент как ассистент).

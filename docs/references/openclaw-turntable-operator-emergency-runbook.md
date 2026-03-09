# OpenClaw Turntable Operator Emergency Runbook

## Purpose
Операторский алгоритм при сбоях интеграции plugin/API/BLE для безопасной остановки движения.

## Emergency triggers
- Ошибка `STOP_FAILED`.
- Повторяющиеся `MOVE_FAILED` (2+ подряд).
- Потеря связи с API (`UPSTREAM_TIMEOUT` / `UPSTREAM_UNAVAILABLE`) во время сценария движения.
- Физическое поведение стола не соответствует командам.

## Immediate response
1. Попробовать `turntable_stop`.
2. Выполнить `turntable_state`.
3. Если `status != IDLE` или `stop` неуспешен — остановить автономный сценарий и перейти к manual mode.

## Manual recovery path
1. Отключить plugin для агента:
   - `plugins.entries.turntable.enabled=false` или убрать tool allowlist у агента.
2. Проверить host API:
   - `bash scripts/run_turntable_host_api.sh <BLE_ADDRESS> 127.0.0.1 18000`
   - `curl -s -X POST http://127.0.0.1:18000/state`
3. Выполнить аварийную команду напрямую в API:
   - `curl -s -X POST http://127.0.0.1:18000/stop`
4. После стабилизации:
   - `state -> home -> move_to small step -> state`.

## Escalation
- Если `STOP_FAILED` повторяется, передать управление человеку/оператору стенда.
- Зафиксировать incident:
  - время;
  - входная команда;
  - error payload;
  - последняя успешная команда;
  - действия восстановления.

## Rollback to host-only mode
1. Отключить plugin в OpenClaw.
2. Работать только через `scripts/turntable_tool_cli.py` или прямой HTTP API.
3. Вернуть plugin только после успешного smoke + manual safety checks.

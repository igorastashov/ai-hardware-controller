# OpenClaw Turntable Plugin v1 Release Notes

## Version
v1 (MVP external plugin integration baseline)

## Included
- Новый пакет `integrations/openclaw-turntable-plugin`.
- Конфиг plugin:
  - `baseUrl`
  - `timeoutMs`
  - `retry.maxAttempts`
  - `retry.backoffMs`
  - `safety.maxTiltDeg`
  - `safety.minRotateSpeed`
  - `safety.minTiltSpeed`
  - `allowSideEffects`
  - `commandGapMs`
  - `idempotencyWindowMs`
- Реализованные tools:
  - `turntable_state`
  - `turntable_home`
  - `turntable_move_to`
  - `turntable_return_base`
  - `turntable_stop`
  - `turntable_commissioning_first_run` (optional)
- Safety policy в plugin runtime:
  - pre-state check перед motion;
  - блокировка при non-IDLE;
  - anti-flood guard;
  - idempotency window для повторных `move_to`;
  - stop-on-ambiguity при ошибке движения.
- Тесты plugin:
  - unit (`config`, `mappers`);
  - contract (`plugin.contract`);
  - smoke entrypoint.

## Operational notes
- Side-effect tools отключены по умолчанию (`allowSideEffects=false`).
- Для production-like использования включать tools только через agent allowlist.
- Hardware acceptance и E2E сценарии требуют реального стенда.

## Known limitations
- Компонент не реализует closed-loop servo control.
- Поведение depends on upstream API contract (`scripts/turntable_tool_api.py`).
- Без OpenClaw runtime в этом репозитории невозможно автоматически подтвердить visibility policy на конкретной инсталляции OpenClaw.

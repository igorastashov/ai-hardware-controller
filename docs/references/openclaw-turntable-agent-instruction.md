# OpenClaw Turntable Agent Instruction

## Version
MVP instruction set (2026-03-06)

## Agent objective
- Безопасно управлять Revopoint Dual-axis Turntable через tool-контракт.
- Предпочитать предсказуемость и отказоустойчивость над агрессивной скоростью команд.

## Allowed tool surface
- `turntable_state()`
- `turntable_home()`
- `turntable_move_to(rotation_deg, tilt_deg, rotate_speed_value?, tilt_speed_value?)`
- `turntable_return_base()`
- `turntable_stop()`

## Mandatory safety policy
1. Всегда начинать с `turntable_state`.
2. Если `ble_connected=false`, не отправлять motion; сначала восстановить соединение.
3. Если `status != IDLE`, не отправлять новую motion-команду.
4. При `DEVICE_BUSY` не ретраить сразу; подождать и повторить `state`.
5. При любой неоднозначности физического состояния вызывать `turntable_stop`.

## Motion policy
- Использовать absolute target только через `turntable_move_to`.
- Не посылать несколько motion-команд параллельно.
- Для step-by-step сценариев:
  - small increments для tilt;
  - ограничивать число команд в секунду (без command flooding).

## Bounds and validation
- `tilt_deg` в `[-30, 30]`.
- Provisional speed bounds:
  - rotate: `[18, 90]`
  - tilt: `[40, 90]`
- При `VALIDATION_ERROR` скорректировать параметры, а не повторять те же.

## Timing assumptions
- Completion model timing-based (не по live encoder):
  - учитывает startup delay + estimated movement time + safety buffer.
- Не использовать текущие query-поля как абсолютно достоверную live-позу.

## Error handling contract
- `BLE_CONNECT_FAILED` / `BLE_DISCONNECT_FAILED`: перейти в reconnect workflow.
- `MOVE_FAILED`: запросить `state`, при необходимости `stop`, затем безопасный повтор.
- `STOP_FAILED`: повысить приоритет оператора/человека (manual intervention).

## Recommended control loop
1. `state`
2. `home` (однократно в начале сессии)
3. `move_to`
4. `state`
5. если результат нештатный -> `stop` -> `state` -> решение о продолжении

## Base return policy
- Для возврата в базу использовать `turntable_return_base`.
- Если `home` уже выполнялся в текущей сессии, базой считается `software_zero`.
- Если `home` не выполнялся, используется `power_on_zero` fallback (rotate `TOZERO` + tilt `0`).

## Out of scope
- High-frequency balance control (уровень servo/PID с быстрым feedback loop).
- Автокалибровка абсолютной физической позы без внешнего эталона.

# OpenClaw Turntable Tool Contract

## Purpose
- Финальный контракт ручек для интеграции в OpenClaw.
- Определяет функционал, входы, выходы, коды ошибок и безопасный порядок вызовов.

## Tool handles
- `turntable_state`
- `turntable_home`
- `turntable_move_to`
- `turntable_return_base`
- `turntable_stop`
- `turntable_commissioning_first_run`

## Functional checklist
- `turntable_state`
  - возвращает текущий runtime статус и виртуальную позу
  - поля: `rotation_deg`, `tilt_deg`, `status`, `ble_connected`, `zero_calibrated`, `reference_frame`
- `turntable_home`
  - фиксирует текущую позу как `software_zero`
  - сбрасывает виртуальные углы в `0,0`
- `turntable_move_to(rotation_deg, tilt_deg, rotate_speed_value?, tilt_speed_value?)`
  - absolute API для агента
  - внутри: shortest-path по rotate
  - валидация угла tilt и speed bounds
  - сериализация команд через single-flight mutex
- `turntable_return_base()`
  - если `software_zero` есть: возвращает в `(0,0)` относительно software zero
  - иначе: `+CT,TOZERO;` для rotate и `+CR,TILTVALUE=0;` для tilt
- `turntable_stop()`
  - аварийный стоп обеих осей (`CT,STOP` + `CR,STOP`)
- `turntable_commissioning_first_run(max_capability?, include_busy_check?, include_stop_check?)`
  - автоматизированный first-run на реальном устройстве
  - возвращает `ready` и список checks с деталями по каждому шагу

## Input constraints
- `tilt_deg`: `[-30, 30]`
- Provisional speed bounds:
  - `rotate_speed_value`: `[18, 90]`
  - `tilt_speed_value`: `[40, 90]`

## Output schema (common)
- success:
  - `{ "ok": true, "result": { ... } }`
- failure:
  - `{ "ok": false, "error": { "code": "...", "message": "...", "http_status": N } }`

## Error codes (current)
- `BLE_CONNECT_FAILED` (503)
- `BLE_DISCONNECT_FAILED` (500)
- `DEVICE_BUSY` (409)
- `TILT_OUT_OF_RANGE` (422)
- `VALIDATION_ERROR` (422)
- `MOVE_FAILED` (500)
- `RETURN_BASE_FAILED` (500)
- `STOP_FAILED` (500)

## Operational policy
- Перед motion всегда проверять `turntable_state`.
- При `status != IDLE` не отправлять новую motion команду.
- При любой неоднозначности физического состояния выполнять `turntable_stop`.
- Для session-consistent coordinates выполнять `turntable_home` в начале рабочей сессии.

## Known limits
- Completion model timing-based (не encoder-grade).
- Для high-frequency balancing control (реальный servo loop) текущий контур не предназначен.
- В Docker Desktop на Windows BLE может быть недоступен из контейнера; для физического commissioning используйте host Python процесс.

# Turntable Tool CLI Runbook

## Version
MVP (2026-03-06)

## Purpose
- Быстрый операторский сценарий для ручной работы через `scripts/turntable_tool_cli.py`.
- Используется перед/во время интеграции с OpenClaw для валидации поведения ручек.

## Preconditions
- Turntable включен и доступен по BLE.
- Python окружение проекта активно (`.venv`).
- Рабочий адрес (по умолчанию): `D3:36:39:34:5D:29`.

## Base commands

```powershell
.\.venv\Scripts\python.exe "scripts/turntable_tool_cli.py" --address "D3:36:39:34:5D:29" state
.\.venv\Scripts\python.exe "scripts/turntable_tool_cli.py" --address "D3:36:39:34:5D:29" home
.\.venv\Scripts\python.exe "scripts/turntable_tool_cli.py" --address "D3:36:39:34:5D:29" return-base
.\.venv\Scripts\python.exe "scripts/turntable_tool_cli.py" --address "D3:36:39:34:5D:29" stop
```

## Move command

```powershell
.\.venv\Scripts\python.exe "scripts/turntable_tool_cli.py" --address "D3:36:39:34:5D:29" move-to --rotation-deg 30 --tilt-deg 10
```

With explicit speed values:

```powershell
.\.venv\Scripts\python.exe "scripts/turntable_tool_cli.py" --address "D3:36:39:34:5D:29" move-to --rotation-deg 30 --tilt-deg 10 --rotate-speed 18 --tilt-speed 40
```

## Safe operational loop
1. `state` -> проверить `ble_connected=true`, `status=IDLE`.
2. `home` -> зафиксировать программный ноль.
3. `move-to` с умеренными углами.
4. `state` -> убедиться, что runtime вернулся в `IDLE`.
5. При любом сомнении/ошибке -> `stop`.

## Return to base 0
- `return-base` выбирает режим автоматически:
  - `software_zero` (если ранее был `home` в сессии)
  - `power_on_zero` fallback (`+CT,TOZERO;` + `+CR,TILTVALUE=0;`)
- После `return-base` всегда рекомендуется проверить `state`.

## Constraints and ranges
- `tilt_deg` должен быть в пределах `[-30, 30]`.
- Provisional speed bounds:
  - `rotate-speed`: `[18, 90]`
  - `tilt-speed`: `[40, 90]`
- Для rotate используется shortest-path нормализация (внешний absolute target -> внутренний delta).

## Error interpretation
- `DEVICE_BUSY` (409): другая команда движения уже выполняется.
- `VALIDATION_ERROR` (422): невалидный диапазон угла/скорости.
- `MOVE_FAILED` (500): runtime/protocol failure.
- `BLE_CONNECT_FAILED` (503): устройство недоступно, повторить позже.

## Notes
- ACK `+OK;` подтверждает прием команды, но не эквивалентен high-frequency servo control.
- Для сценариев балансировки (высокая частота коррекции) текущий канал/модель не предназначены.

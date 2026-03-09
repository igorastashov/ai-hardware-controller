# Turntable Tool CLI Runbook

## Version
MVP (2026-03-06)

## Purpose
- Быстрый операторский сценарий для ручной работы через `scripts/turntable_tool_cli.py`.
- Используется перед/во время интеграции с OpenClaw для валидации поведения ручек.
- Дополнительно покрывает первый запуск FastAPI-ручек и acceptance на реальной механике.

## Preconditions
- Turntable включен и доступен по BLE.
- Python окружение проекта активно (`.venv`).
- Рабочий адрес (по умолчанию): `D3:36:39:34:5D:29`.
- Основной shell: Git Bash (без PowerShell).

## Quick start (Git Bash)

```bash
py -3 -m pip install -r requirements.txt
bash scripts/run_turntable_host_api.sh D3:36:39:34:5D:29 127.0.0.1 18000
```

Во втором терминале поднимите сетевой Docker gateway:

```bash
docker compose up -d --build
docker compose ps
```

В отдельном терминале:

```bash
curl -sS "http://127.0.0.1:8000/health"                # gateway
curl -sS -X POST "http://127.0.0.1:8000/state"         # proxy -> host BLE API
```

## OpenClaw endpoint

- OpenClaw в контейнере на этом же ПК: `http://host.docker.internal:8000`
- OpenClaw на другом устройстве в LAN: `http://192.168.31.97:8000` (или актуальный IPv4 этого хоста)
- В Docker Desktop на Windows BLE в контейнере обычно недоступен, поэтому compose-сервис работает как HTTP gateway к host BLE API.

## API functional checks (Git Bash)

```bash
curl -sS -X POST "http://127.0.0.1:8000/state"
curl -sS -X POST "http://127.0.0.1:8000/home"
curl -sS -X POST "http://127.0.0.1:8000/move-to" -H "Content-Type: application/json" -d "{\"rotation_deg\":30,\"tilt_deg\":10}"
curl -sS -X POST "http://127.0.0.1:8000/return-base"
curl -sS -X POST "http://127.0.0.1:8000/stop"
```

С явными speed:

```bash
curl -sS -X POST "http://127.0.0.1:8000/move-to" -H "Content-Type: application/json" -d "{\"rotation_deg\":30,\"tilt_deg\":10,\"rotate_speed_value\":18,\"tilt_speed_value\":40}"
```

## One-shot commissioning (recommended first-run)

CLI (самый надежный путь для физической приемки):

```bash
py -3 scripts/turntable_commissioning.py --address "D3:36:39:34:5D:29"
```

Консервативный профиль:

```bash
py -3 scripts/turntable_commissioning.py --address "D3:36:39:34:5D:29" --safe-profile
```

Через HTTP-ручку:

```bash
curl -sS -X POST "http://127.0.0.1:8000/commissioning/first-run" \
  -H "Content-Type: application/json" \
  -d "{\"max_capability\":true,\"include_busy_check\":true,\"include_stop_check\":true}"
```

Полный first-run без параметров (отдельная ручка):

```bash
curl -sS -X POST "http://127.0.0.1:8000/commissioning/first-run/full"
```

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
- Если API запущен в Docker container и возвращает `BLE_CONNECT_FAILED`, используйте host запуск через `bash scripts/run_turntable_host_api.sh ...`.

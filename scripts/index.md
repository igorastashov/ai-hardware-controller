# Engineering Harness — Каталог скриптов

> Эта папка содержит скрипты автоматической проверки (Engineering Harness).
> Агент обязан использовать их для валидации своей работы.
>
> Подробнее о философии Harness Engineering — в `docs/index.md`, секция B.6.

## Принципы

1. **Каждая повторяющаяся ошибка агента должна стать проверкой.** Если агент ошибся и ошибку можно обнаружить автоматически — добавь скрипт или расширь `verify.sh`.
2. **У каждого скрипта есть контракт.** Описание: что делает, какие аргументы принимает, что возвращает.
3. **Скрипты — это тоже код.** Они версионируются, тестируются и документируются.

## Реестр скриптов

### `verify.sh` — Главный скрипт валидации

| Параметр | Значение |
|---|---|
| **Назначение** | Запускает все проверки: линтинг, типизация, тесты |
| **Аргументы** | Нет (запускает полный набор) |
| **Возвращает** | Exit code 0 = всё ок, non-zero = есть ошибки |
| **Когда вызывать** | Перед завершением любой задачи (обязательно) |
| **Пример вызова** | `bash scripts/verify.sh` |

### `turntable_discover.py` — Разведка BLE-профиля поворотного стола

| Параметр | Значение |
|---|---|
| **Назначение** | Сканирует BLE-устройства, выбирает целевой turntable и сохраняет GATT-профиль в JSON-артефакт |
| **Аргументы** | `--target-name`, `--target-address`, `--output`, `--scan-seconds` |
| **Возвращает** | Exit code 0 + JSON отчёт с `scan`, `gatt`, `errors` |
| **Когда вызывать** | Перед разработкой driver/tool интерфейсов и при смене hardware revision |
| **Пример вызова** | `python scripts/turntable_discover.py --target-name REVO_DUAL_AXIS_TABLE` |

### `turntable_protocol_probe.py` — Узкая разведка протокола (без motion)

| Параметр | Значение |
|---|---|
| **Назначение** | Подключается к turntable, включает notify на выбранной характеристике, отправляет query-команду и сохраняет ответы в JSON |
| **Аргументы** | `--target-address` (required), `--char-uuid`, `--command`, `--encoding`, `--append-crlf`, `--wait-seconds`, `--output` |
| **Возвращает** | Exit code 0 + JSON отчёт с результатом записи, количеством notify и декодированием payload |
| **Когда вызывать** | Перед реализацией runtime parser/ACK модели и подтверждением `state_confidence=HIGH` |
| **Пример вызова** | `python scripts/turntable_protocol_probe.py --target-address D3:36:39:34:5D:29` |

### `turntable_motion_characterize.py` — Проверка телеметрии вокруг движения

| Параметр | Значение |
|---|---|
| **Назначение** | Делает baseline queries, отправляет motion-команду и выполняет polling query, чтобы оценить семантику телеметрии |
| **Аргументы** | `--target-address` (required), `--move-command` (required), `--poll-interval-seconds`, `--poll-total-seconds`, `--output` |
| **Возвращает** | Exit code 0 + JSON-артефакт с baseline, ACK и серией polling-сэмплов |
| **Когда вызывать** | Перед финализацией модели `BUSY -> IDLE` и правил `state_confidence` |
| **Пример вызова** | `python scripts/turntable_motion_characterize.py --target-address D3:36:39:34:5D:29 --move-command "+CT,TURNANGLE=10;" --output docs/references/artifacts/motion-char-rotate10.json` |

### `turntable_busy_characterize.py` — Проверка busy/queue на быстрых командах

| Параметр | Значение |
|---|---|
| **Назначение** | Отправляет 2 motion-команды с малым интервалом, слушает notify и фиксирует ответы (`OK/FAIL`) |
| **Аргументы** | `--target-address` (required), `--command-1`, `--command-2`, `--gap-seconds`, `--listen-seconds`, `--output` |
| **Возвращает** | Exit code 0 + JSON-артефакт с временем отправки команд и всеми notify-сообщениями |
| **Когда вызывать** | Перед внедрением runtime mutex/очереди для agent tools |
| **Пример вызова** | `python scripts/turntable_busy_characterize.py --target-address D3:36:39:34:5D:29 --command-1 "+CT,TURNANGLE=20;" --command-2 "+CR,TILTVALUE=5;" --output docs/references/artifacts/busy-char-cross-axis.json` |

### `turntable_runtime_singleflight.py` — Черновик runtime state machine

| Параметр | Значение |
|---|---|
| **Назначение** | Реализует программный mutex (`single-flight`) для motion-команд, parser кадров и timing-based completion |
| **Аргументы** | Нет CLI (импортируемый runtime-модуль) |
| **Возвращает** | API-класс `TurntableRuntimeSingleFlight` и типы состояния/кадров |
| **Когда вызывать** | При интеграции motion tool-ручек для агента |
| **Пример использования** | `from turntable_runtime_singleflight import TurntableRuntimeSingleFlight` |

### `turntable_tool_adapter.py` — Контракт tool-ручек для агента

| Параметр | Значение |
|---|---|
| **Назначение** | Оборачивает runtime в стабильные tool-методы (`state/home/move_to/stop`) с JSON-ответами и кодами ошибок |
| **Аргументы** | Нет CLI (импортируемый модуль) |
| **Возвращает** | Класс `TurntableToolAdapter` с методами `turntable_state`, `turntable_home`, `turntable_move_to`, `turntable_stop` |
| **Когда вызывать** | При интеграции в OpenClaw/agent tool layer |
| **Пример использования** | `from turntable_tool_adapter import TurntableToolAdapter` |

### `turntable_tool_adapter_smoke.py` — Smoke-проверка tool-контракта

| Параметр | Значение |
|---|---|
| **Назначение** | Проверяет форму JSON-ответов tool-адаптера и базовые сценарии (`home/move_to/state/stop`) без реального BLE-устройства |
| **Аргументы** | Нет |
| **Возвращает** | Exit code 0 при успешных smoke-checks, 1 при провале |
| **Когда вызывать** | После изменений в `turntable_tool_adapter.py` |
| **Пример вызова** | `python scripts/turntable_tool_adapter_smoke.py` |

---

> **Как добавить новый скрипт:**
> 1. Создай файл в `scripts/`.
> 2. Добавь описание в эту таблицу (формат — как у `verify.sh`).
> 3. Если скрипт должен вызываться агентом — добавь упоминание в `AGENTS.md`.

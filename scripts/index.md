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

### `check_docs_blockers_sync.py` — Проверка синхронности критичных правил

| Параметр | Значение |
|---|---|
| **Назначение** | Проверяет, что чеклисты первого подтверждения в `AGENTS.md` и `.cursor/rules/repo-conventions.mdc` синхронизированы и содержат критичные маркеры |
| **Аргументы** | Нет |
| **Возвращает** | Exit code 0 при синхронности, 1 при рассинхроне; печатает структурированный JSON-отчёт |
| **Когда вызывать** | После изменений в `AGENTS.md` или `.cursor/rules/repo-conventions.mdc` (а также через `verify.sh`) |
| **Пример вызова** | `python scripts/check_docs_blockers_sync.py` |

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
| **Примечание** | Скрипт использует retry connect для transient BLE проблем |

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

### `turntable_tool_adapter_contract_test.py` — Контрактные тесты ручек

| Параметр | Значение |
|---|---|
| **Назначение** | Проверяет схему ответов, busy/validation политику, return-base и shortest-path логику без реального BLE |
| **Аргументы** | Нет |
| **Возвращает** | Exit code 0 при прохождении всех контрактных проверок |
| **Когда вызывать** | После изменений в runtime/adapter/CLI контракте |
| **Пример вызова** | `python scripts/turntable_tool_adapter_contract_test.py` |

### `turntable_timing_probe.py` — Калибровка timing-модели движения

| Параметр | Значение |
|---|---|
| **Назначение** | Выполняет матрицу `speed + move` и сохраняет временную ленту ACK/notify для калибровки completion-модели |
| **Аргументы** | `--target-address`, `--axis`, `--speed-values`, `--move-value`, `--settle-seconds`, `--output` |
| **Возвращает** | JSON-артефакт с run-by-run событиями и шаблоном для ручных наблюдений |
| **Когда вызывать** | Перед финализацией timing-based completion в runtime |
| **Пример вызова** | `python scripts/turntable_timing_probe.py --target-address D3:36:39:34:5D:29 --axis rotate --speed-values 8,12,20 --move-value 30 --output docs/references/artifacts/timing-rotate.json` |
| **Примечание** | Скрипт использует retry connect и завершает с safety stop |

### `turntable_speed_decode_probe.py` — Декодирование валидных speed-команд

| Параметр | Значение |
|---|---|
| **Назначение** | Проверяет матрицу значений speed-команд и фиксирует accepted/rejected/timeout по каждой оси |
| **Аргументы** | `--target-address`, `--axis`, `--values`, `--output` |
| **Возвращает** | JSON-артефакт с полным ответом и сводкой по валидным значениям |
| **Когда вызывать** | Перед использованием speed-параметров в timing completion модели |
| **Пример вызова** | `python scripts/turntable_speed_decode_probe.py --target-address D3:36:39:34:5D:29 --axis rotate --values 1,2,4,8,12,20 --output docs/references/artifacts/speed-rotate.json` |
| **Примечание** | Скрипт использует retry connect и добавляет safety stop в конце |

### `turntable_dual_axis_probe.py` — Проверка квази-одновременного rotate+tilt

| Параметр | Значение |
|---|---|
| **Назначение** | Отправляет speed+move для двух осей с минимальным gap и фиксирует timeline/notify для оценки concurrency-реакции |
| **Аргументы** | `--target-address`, `--rotate-speed`, `--tilt-speed`, `--rotate-angle`, `--tilt-target`, `--gap-seconds`, `--observe-seconds`, `--output` |
| **Возвращает** | JSON-артефакт с timeline отправки и notify-событиями |
| **Когда вызывать** | При валидации сценариев одновременной работы осей и оценки command-level латентности |
| **Пример вызова** | `python scripts/turntable_dual_axis_probe.py --target-address D3:36:39:34:5D:29 --rotate-speed 18 --tilt-speed 40 --rotate-angle 120 --tilt-target 20 --output docs/references/artifacts/dual-axis-probe.json` |

### `turntable_tool_cli.py` — CLI для будущих agent-ручек

| Параметр | Значение |
|---|---|
| **Назначение** | Вызывает `state/home/move-to/stop` через адаптер, печатает JSON-результат |
| **Аргументы** | Глобальный `--address`, команды: `state`, `home`, `return-base`, `stop`, `move-to --rotation-deg --tilt-deg [--rotate-speed --tilt-speed]` |
| **Возвращает** | Exit code 0 на успешный `ok=true`, иначе 1 |
| **Когда вызывать** | Для ручной проверки контракта tool-слоя перед интеграцией в OpenClaw |
| **Пример вызова** | `python scripts/turntable_tool_cli.py --address D3:36:39:34:5D:29 move-to --rotation-deg 30 --tilt-deg 10 --rotate-speed 18 --tilt-speed 40` |

---

> **Как добавить новый скрипт:**
> 1. Создай файл в `scripts/`.
> 2. Добавь описание в эту таблицу (формат — как у `verify.sh`).
> 3. Если скрипт должен вызываться агентом — добавь упоминание в `AGENTS.md`.

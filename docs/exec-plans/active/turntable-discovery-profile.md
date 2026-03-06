# Turntable Discovery and Device Profile

**Status:** In Progress
**Branch:** `turtable-agent`
**Created:** 2026-03-06
**Author:** Cursor Agent

---

## 1. Context & Purpose (Контекст и цель)

Подготовить безопасную основу для будущего управления Revopoint Dual-axis Turntable через agent tools.

- **Бизнес-цель:** получить надежные tool-ручки для ИИ-агента без неуправляемого поведения железа.
- **Техническая цель:** выполнить BLE-разведку, зафиксировать профиль устройства и довести runtime/tool-контракт до интеграционного MVP-уровня.
- **Связанные документы:**
  - Design Doc: `docs/design-docs/core-beliefs.md`
  - Product Spec: `docs/product-specs/turntable-agent-goal.md`

## 2. Execution Steps (Шаги выполнения)

- [x] Шаг 1: Согласовать базовые ограничения устройства и требования к интерфейсам. (2026-03-06 17:00)
- [x] Шаг 2: Вынести лимиты и тайминги устройства в конфиг без hardcode в runtime-коде. (2026-03-06 17:00)
- [x] Шаг 3: Добавить discovery-скрипт для BLE scan + GATT profile capture с JSON-отчетом. (2026-03-06 17:00)
- [x] Шаг 4: Создать device profile в документации и связать его с discovery artifact. (2026-03-06 17:00)
- [x] Шаг 5: Прогнать discovery на реальном устройстве и обновить профиль по фактическим UUID/feedback. (2026-03-06 17:00)
- [x] Шаг 6: Прогнать `scripts/verify.sh` (линт/тесты в проекте пока заглушки). (2026-03-06 17:00)
- [x] Шаг 7: Добавить protocol probe (notify + query без motion) и артефакт отчета. (2026-03-06 17:00)
- [x] Шаг 8: Проверить терминатор команд (`;` vs `;\\r\\n`) и зафиксировать наблюдение в device profile. (2026-03-06 17:00)
- [x] Шаг 9: Выполнить query-matrix для rotate и определить рабочий query-префикс. (2026-03-06 17:00)
- [x] Шаг 10: Проверить формат ACK на безопасных stop-командах (`+CT,STOP;`, `+CR,STOP;`). (2026-03-06 17:00)
- [x] Шаг 11: Выполнить минимальную motion-матрицу (малые углы) и сравнить baseline/post-query. (2026-03-06 17:00)
- [x] Шаг 12: Выполнить motion characterization с polling (`rotate=10`, `tilt=5`) и уточнить модель телеметрии. (2026-03-06 17:00)
- [x] Шаг 13: Проверить busy/queue-поведение на быстрых последовательностях команд. (2026-03-06 17:00)
- [x] Шаг 14: Добавить runtime-черновик state machine с single-flight mutex и timing completion. (2026-03-06 17:00)
- [x] Шаг 15: Добавить tool-адаптер с JSON-контрактом (`state/home/move_to/stop`) для будущей интеграции с агентом. (2026-03-06 17:00)
- [x] Шаг 16: Добавить Product Spec (DoD) и smoke-harness для tool-адаптера. (2026-03-06 17:00)
- [x] Шаг 17: Запустить timing probe на 2 осях и выявить поведение speed-команд. (2026-03-06 17:00)
- [x] Шаг 18: Выполнить speed decode matrix и определить принятые/отклоненные диапазоны. (2026-03-06 17:00)
- [x] Шаг 19: Уточнить speed protocol (query-команды + пороги по осям). (2026-03-06 17:00)
- [x] Шаг 20: Запустить калибровочные прогоны по валидным speed-диапазонам (rotate/tilt). (2026-03-06 17:00)
- [x] Шаг 21: Применить ручную калибровку времени (startup + deg/s) в runtime timing model. (2026-03-06 17:00)
- [x] Шаг 22: Добавить speed validation в runtime/tool и retry connect для probe-скриптов. (2026-03-06 17:00)
- [x] Шаг 23: Добавить tool CLI и проверить dual-axis near-simultaneous dispatch. (2026-03-06 17:00)
- [x] Шаг 24: Добавить runbook/agent instruction и контракт ручек для OpenClaw. (2026-03-06 17:00)
- [x] Шаг 25: Добавить стратегию возврата в базу 0 (`software_zero` / `power_on_zero`). (2026-03-06 17:00)
- [x] Шаг 26: Финализировать тестовый план и backlog работ будущего агента. (2026-03-06 17:00)
- [x] Шаг 24: Добавить runbook и инструкцию для OpenClaw-агента в references. (2026-03-06 17:00)

> При выполнении шага: `- [x] Шаг 1: Описание. (YYYY-MM-DD HH:MM)`

## 3. Surprises & Discoveries (Сюрпризы и находки)

- **(2026-03-06 17:00) Сюрприз:** рабочий терминал с BLE-сканированием показал `REVO_DUAL_AXIS_TABLE`, но в отдельном запрошенном terminal file был неверный путь.
  - **Контекст:** проверка ветки и истории команд из terminal snapshot.
  - **Решение:** опора на фактически существующий terminal file с подтверждением обнаружения устройства.
  - **Harness Update:** автоматизация не требуется на этом этапе, так как это инфраструктурный контекст IDE, а не код проекта.
- **(2026-03-06 17:00) Сюрприз:** в текущей версии bleak объект `BLEDevice` не гарантирует поле `rssi`.
  - **Контекст:** первый запуск discovery падал на извлечении `item.rssi`.
  - **Решение:** безопасный доступ через `getattr(item, "rssi", None)` и аналогично для metadata.
  - **Harness Update:** зафиксировано в `scripts/turntable_discover.py`; отдельный тест пока не добавлен, так как тестовый контур BLE еще не настроен.
- **(2026-03-06 17:00) Сюрприз:** одна и та же характеристика может быть одновременно write-without-response и notify/read, что не гарантирует ACK прикладного уровня.
  - **Контекст:** анализ GATT-профиля и подготовка protocol probe.
  - **Решение:** отдельный probe-скрипт с фиксацией факта записи и реальных notify payload в артефакт JSON.
  - **Harness Update:** `scripts/turntable_protocol_probe.py` + `docs/references/artifacts/revopoint-dual-axis-protocol-probe.json`.
- **(2026-03-06 17:00) Сюрприз:** ответ на `+QR,TILTANGLE;` пришел не в формате `+QR,...=...;`, а в унифицированном формате `+DATA=min,max,current;`.
  - **Контекст:** запуск protocol probe на `FFE1`.
  - **Решение:** зафиксировать формат ответа как наблюдение, не как окончательный контракт, до повторной валидации.
  - **Harness Update:** второй артефакт с `;\\r\\n` (`docs/references/artifacts/revopoint-dual-axis-protocol-probe-crlf.json`) подтвердил тот же ответ.
- **(2026-03-06 17:00) Сюрприз:** для rotate query используется префикс `QT`, а не `QR`.
  - **Контекст:** `+QR,TURNANGLE;` и `+QR,ROTATEANGLE;` вернули `+FAIL,ERR=001;`, но `+QT,TURNANGLE;` вернул `+DATA=0,360,1.0;`.
  - **Решение:** зафиксировать query matrix в device profile и использовать `+QT,TURNANGLE;` как текущий рабочий rotate query.
  - **Harness Update:** артефакты `...probe-turnangle.json`, `...probe-qr-rotateangle.json`, `...probe-qt-turnangle.json`, `...probe-qt-turnangle-crlf.json`.
- **(2026-03-06 17:00) Сюрприз:** команды `+CT,STOP;` и `+CR,STOP;` возвращают явный ACK `+OK;` по notify-каналу.
  - **Контекст:** безопасный probe без запуска движения.
  - **Решение:** использовать `+OK;` / `+FAIL,ERR=...;` как базовую модель ACK/ошибок в будущем runtime parser.
  - **Harness Update:** `...protocol-probe-stop-ct.json` и `...protocol-probe-stop-cr.json`.
- **(2026-03-06 17:00) Сюрприз:** минимальные motion-команды (`+CT,TURNANGLE=2;`, `+CR,TILTVALUE=1;`) дали `+OK;`, но post-query значения в этом прогоне не изменились.
  - **Контекст:** motion probe с baseline -> command -> post-query -> stop.
  - **Решение:** считать ACK подтверждением принятия команды, но не подтверждением фактического завершенного перемещения.
  - **Harness Update:** артефакты `...motion-probe-01..08.json`.
- **(2026-03-06 17:00) Сюрприз:** в characterization с polling (`+CT,TURNANGLE=10;`, `+CR,TILTVALUE=5;`) query-поля остались стабильными, несмотря на физически наблюдаемое движение.
  - **Контекст:** 2 сценария по 6 секунд polling, 12 сэмплов каждый.
  - **Решение:** трактовать текущие query-ответы как неполный источник состояния, а завершение движения определять по расчетной модели времени + safety buffer.
  - **Harness Update:** `revopoint-motion-char-rotate10.json`, `revopoint-motion-char-tilt5.json`, скрипт `scripts/turntable_motion_characterize.py`.
- **(2026-03-06 17:00) Сюрприз:** устройство принимает быстрые последовательные команды (gap 100 мс) и отвечает `+OK;` без `BUSY/FAIL`.
  - **Контекст:** cross-axis (`CT` -> `CR`) и same-axis (`CT` -> `CT`) сценарии.
  - **Решение:** зафиксировать, что сериализация/блокировки должны быть на стороне runtime, а не делегированы устройству.
  - **Harness Update:** `revopoint-busy-char-cross-axis.json`, `revopoint-busy-char-same-axis.json`, скрипт `scripts/turntable_busy_characterize.py`.
- **(2026-03-06 17:00) Сюрприз:** физически наблюдаемое движение ("в одну сторону, затем в другую") может не отражаться в query-телеметрии.
  - **Контекст:** пользователь подтвердил фактическое перемещение на rotate/tilt в живом тесте.
  - **Решение:** runtime completion не привязывать к текущему значению `+DATA` третьего поля; использовать timing-модель и safety buffer.
  - **Harness Update:** runtime-черновик `scripts/turntable_runtime_singleflight.py`.
- **(2026-03-06 17:00) Сюрприз:** для long-running agent integration нужен стабильный tool-контракт независимо от внутренних изменений runtime.
  - **Контекст:** переход от исследования протокола к интеграционному слою.
  - **Решение:** добавить отдельный adapter-модуль с фиксированным JSON-форматом ответов и кодами ошибок.
  - **Harness Update:** `scripts/turntable_tool_adapter.py`.
- **(2026-03-06 17:00) Сюрприз:** для длительной работы не хватает явного Product DoD; только технического плана недостаточно.
  - **Контекст:** переход к интеграционному этапу и необходимость единых критериев готовности.
  - **Решение:** добавить product spec с приемочными критериями и smoke-проверку контрактного слоя.
  - **Harness Update:** `docs/product-specs/turntable-agent-goal.md`, `scripts/turntable_tool_adapter_smoke.py`.
- **(2026-03-06 17:00) Сюрприз:** speed-команды в тестовых диапазонах дают `FAIL` (`ERR=004`/`ERR=007`), а команды движения при этом подтверждаются `OK`.
  - **Контекст:** timing probe на rotate (`8,12,20`) и tilt (`3,5,7`).
  - **Решение:** временно исключить speed-команды из completion-модели до декодирования валидных диапазонов/формата.
  - **Harness Update:** `scripts/turntable_timing_probe.py`, артефакты `revopoint-timing-rotate-30.json`, `revopoint-timing-tilt-10.json`.
- **(2026-03-06 17:00) Сюрприз:** rotate speed принимает только часть диапазона (`20`, `30`), tilt speed в протестированном наборе полностью отклоняется.
  - **Контекст:** матричный probe значений speed-команд по двум осям.
  - **Решение:** считать speed decode отдельно по осям; для tilt искать альтернативный командный ключ/формат.
  - **Harness Update:** `scripts/turntable_speed_decode_probe.py`, артефакты `revopoint-speed-decode-rotate.json`, `revopoint-speed-decode-tilt.json`.
- **(2026-03-06 17:00) Сюрприз:** speed-протокол асимметричен и имеет пороги принятия: rotate >=18, tilt >=40 (в тестовом окне), query тоже разный (`QT,TURNSPEED` vs `QR,TILTSPEED`).
  - **Контекст:** targeted probes после speed-matrix.
  - **Решение:** добавить provisional bounds в конфиг и использовать только как валидационные guard-rails до калибровки deg/s.
  - **Harness Update:** `revopoint-speed-decode-tilt-high-range.json`, `revopoint-speed-decode-tilt-threshold.json`, `revopoint-speed-decode-rotate-threshold.json`, speed-query артефакты.
- **(2026-03-06 17:00) Сюрприз:** калибровочный прогон tilt может временно падать с `BleakDeviceNotFoundError`, но повторный запуск проходит штатно.
  - **Контекст:** первый запуск `timing_probe` для tilt вернул `runs=0` из-за отсутствия устройства в момент коннекта.
  - **Решение:** повторный прогон и фиксация успешного артефакта; учитывать transient BLE availability в процедуре.
  - **Harness Update:** `revopoint-timing-tilt-20-calibration-rerun.json`.
- **(2026-03-06 17:00) Сюрприз:** фактическая длительность движения существенно зависит от startup delay и не совпадает с "голой" формулой по углу.
  - **Контекст:** пользователь дал ручные наблюдения start/finish по 6 калибровочным сценариям.
  - **Решение:** включить в модель отдельные startup delays по осям и консервативные deg/s значения.
  - **Harness Update:** обновлен `MOTION_TIMING` в `scripts/turntable_config.py`, уточнена формула в `scripts/turntable_runtime_singleflight.py`.
- **(2026-03-06 17:00) Сюрприз:** transient BLE-сбои (`DeviceNotFound`) и невалидные speed значения ломают полевые прогоны без явной защиты на уровне runtime/probe.
  - **Контекст:** периодические ошибки connect в calibration-процессе и speed decode результаты с осевыми порогами.
  - **Решение:** добавить retry connect в probe-скрипты и speed bounds в runtime валидацию (`set_rotate_speed`, `set_tilt_speed`).
  - **Harness Update:** `turntable_protocol_probe.py`, `turntable_timing_probe.py`, `turntable_speed_decode_probe.py`, `turntable_runtime_singleflight.py`, `turntable_tool_adapter.py`.
- **(2026-03-06 17:00) Сюрприз:** командный ACK на dual-axis dispatch приходит быстро (десятки миллисекунд), но это не эквивалентно физической высокочастотной стабилизации.
  - **Контекст:** `dual_axis_probe` с gap 50ms и проверкой `speed+move` для обеих осей.
  - **Решение:** выделить agent CLI слой и явно разделять command-level latency vs motion-level latency в документации.
  - **Harness Update:** `scripts/turntable_dual_axis_probe.py`, `scripts/turntable_tool_cli.py`, артефакт `revopoint-dual-axis-concurrency-probe.json`.
- **(2026-03-06 17:00) Сюрприз:** без явной инструкции агенту легко спутать "быстрый ACK" и "быструю физику".
  - **Контекст:** обсуждение сценария балансировки и dual-axis поведения.
  - **Решение:** оформить отдельный agent instruction с обязательной safety policy и out-of-scope разделом.
  - **Harness Update:** `docs/references/openclaw-turntable-agent-instruction.md`, `docs/references/turntable-tool-cli-runbook.md`.
- **(2026-03-06 17:00) Сюрприз:** у "базы 0" есть два валидных смысла (software session zero и hardware power-on zero).
  - **Контекст:** требование пользователя продумать возврат в исходную базу.
  - **Решение:** добавить отдельную ручку `turntable_return_base` с авто-выбором режима.
  - **Harness Update:** `scripts/turntable_tool_adapter.py`, `scripts/turntable_tool_cli.py`, docs references.
- **(2026-03-06 17:00) Сюрприз:** для завершения инфраструктуры под агента недостаточно runbook-инструкций — нужен отдельный test plan и backlog будущей агентной работы.
  - **Контекст:** запрос на "шлифовку до конца" и формализацию задач тестирования.
  - **Решение:** добавить contract test script, тест-план и документ задач будущего агента.
  - **Harness Update:** `scripts/turntable_tool_adapter_contract_test.py`, `docs/references/openclaw-turntable-test-plan.md`, `docs/references/openclaw-turntable-future-agent-work.md`.

## 4. Decision Trace (Журнал решений)

| Решение | Альтернативы | Почему выбрано | Дата |
|---|---|---|---|
| Держать отдельный discovery-этап до motion-кода | Сразу писать driver команды движения | Снижает риск неверных предположений о UUID/feedback и повышает безопасность | 2026-03-06 |
| Внешний API делать абсолютным (`move_to`) | Относительный (`move_by`) API | Удобнее и безопаснее для LLM-агента; меньше риска накопления ошибочных дельт | 2026-03-06 |
| Лимиты/тайминги вынести в конфиг | Hardcode в драйвере | Проще управлять ревизиями устройства и безопасными значениями | 2026-03-06 |
| Протокол валидировать отдельным query-probe до motion | Сразу писать runtime с предположениями по ACK | Снижаем риск неверной модели state/timeout для агента | 2026-03-06 |
| Проверить обе формы терминатора (`;` и `;\\r\\n`) | Жестко зафиксировать один формат на старте | Уменьшаем риск ложных выводов о парсере на устройстве | 2026-03-06 |
| Проверить query-matrix для rotate | Предположить симметрию `QR` между осями | Фактический протокол оказался асимметричным (`QR` vs `QT`) | 2026-03-06 |
| Проверить ACK на stop до motion | Сразу тестировать ACK только на вращении/наклоне | Минимизируем риск, но подтверждаем формат ответа | 2026-03-06 |
| Сначала малые углы в motion-probe | Сразу проверять крупные углы/длительное движение | Снижаем риски для железа и получаем первую модель ACK | 2026-03-06 |
| Использовать polling characterization до runtime-реализации | Переходить к runtime на предположении "query=live pose" | Данные показали, что query не эквивалентен надежной live-позе | 2026-03-06 |
| Проверить быстрые последовательности до реализации mutex | Предположить, что устройство само даст BUSY | Фактические ответы показали отсутствие явного BUSY/reject | 2026-03-06 |
| Сразу внедрить single-flight runtime ядро | Ждать полной расшифровки live-телеметрии | Позволяет безопасно интегрировать tool-ручки уже сейчас с контролируемыми рисками | 2026-03-06 |
| Отделить tool-контракт от runtime-ядра | Отдавать runtime напрямую во внешний слой | Стабильный API для агента и более безопасная эволюция внутренних механизмов | 2026-03-06 |
| Добавить Product Spec + smoke harness до OpenClaw-интеграции | Согласовывать только по техдокам и ручным проверкам | Снижает риск потери цели и регрессов API-контракта | 2026-03-06 |
| Вынести speed calibration в отдельный этап | Сразу завязывать completion-модель на speed-команды | Текущий протокол speed-команд не стабилен, нужен отдельный decode | 2026-03-06 |
| Разделить speed decode по осям | Искать единый валидный диапазон для rotate/tilt | Фактические ответы показывают разную семантику/валидность команд | 2026-03-06 |
| Зафиксировать наблюдаемые speed bounds как provisional | Игнорировать bounds до полной физической калибровки | Позволяет уже сейчас валидировать вход tool-слоя и избегать явных `FAIL` | 2026-03-06 |
| Калибровать speed->deg/s через ручные наблюдения | Оценивать deg/s только по ACK-телеметрии | Текущая телеметрия не является надежным live-энкодером | 2026-03-06 |
| Включить startup delay в completion estimate | Использовать только `angle/deg_s + buffer` | Ручные замеры показали систематическую задержку старта | 2026-03-06 |
| Валидировать speed bounds на входе runtime | Передавать любые значения и ловить FAIL от устройства | Проактивно снижаем ошибочные команды и упрощаем поведение tool-слоя | 2026-03-06 |
| Разделить CLI/tool слой и probe слой | Вызывать runtime напрямую в ручных тестах | Упрощает интеграцию с OpenClaw и эксплуатационные проверки | 2026-03-06 |
| Зафиксировать agent instruction отдельно от техдока | Полагаться только на знания из runtime-кода | Снижает риск неправильной стратегии вызовов в автономной работе агента | 2026-03-06 |
| Развести `software_zero` и `power_on_zero` как разные reference frames | Считать "0" единственным и всегда абсолютным | Уменьшаем риск логических ошибок при возврате в базу после перезапуска/реконнекта | 2026-03-06 |
| Добавить отдельный test plan + future backlog | Ограничиться только технической реализацией ручек | Обеспечивает управляемый переход к следующему агенту/этапу интеграции | 2026-03-06 |

## 5. Leftover Tech Debt (Оставшийся технический долг)

- [x] Подтвердить поддержку hardware-feedback для `rotate` и `tilt`. (query+notify на `FFE1`)
- [ ] Подтвердить модель завершения команды (ACK/notify или расчетное ожидание).
- [ ] Формализовать тайминговую модель завершения движения (в т.ч. safety buffer) и валидацию на 2-3 скоростях.
- [x] Калибровать соответствие "speed value -> deg/s" для rotate и tilt по ручным наблюдениям.
- [x] Добавить retry-логику коннекта в probe-скрипты для transient BLE not found.
- [x] Спроектировать runtime state machine (IDLE/BUSY/ERROR) и политику single-flight для motion tool.
- [x] Добавить runtime-валидацию и structured error schema в будущий motion runtime.
- [ ] Расширить smoke/harness до сценариев reconnect + BUSY race + STOP override.

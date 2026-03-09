# OpenClaw Turntable External Plugin Integration

**Status:** In Progress
**Branch:** `feature/openclaw-turntable-external-plugin`
**Created:** 2026-03-09
**Author:** Cursor Agent

---

## 1. Context & Purpose (Контекст и цель)

Интегрировать управление физическим turntable в OpenClaw без изменений core OpenClaw, используя внешний plugin-адаптер в этом репозитории.

- **Бизнес-цель:** дать агенту надежный и безопасный способ управлять поворотным столом в реальных сессиях.
- **Техническая цель:** реализовать внешний OpenClaw plugin + skill + конфиг + тестовый контур поверх существующего `scripts/turntable_tool_api.py`.
- **Инвариант архитектуры:** OpenClaw core не изменяется; вся доменная логика интеграции живет в этом репозитории.
- **Базовый endpoint:** `http://192.168.31.97:8000` (вынести в plugin config, не хардкодить в коде plugin runtime).
- **Связанные документы:**
  - Design Doc: `docs/design-docs/core-beliefs.md`
  - Product Spec: `docs/product-specs/turntable-agent-goal.md`
  - References:
    - `docs/references/openclaw-turntable-tool-contract.md`
    - `docs/references/openclaw-turntable-agent-instruction.md`
    - `docs/references/openclaw-turntable-test-plan.md`
    - `docs/references/openclaw-turntable-future-agent-work.md`
    - `docs/references/turntable-tool-cli-runbook.md`

### Preflight Checklist (перед стартом фазы B)

- [ ] Host API поднимается локально и отвечает (`POST /state` возвращает валидный JSON-контракт).
- [ ] Выбран способ подключения plugin в OpenClaw (CLI install или `plugins.load.paths`).
- [ ] Подтверждено, что side-effect tools будут включены только через allowlist.
- [ ] Зафиксирован fallback-сценарий при недоступном API (structured error + no silent success).

## 2. Target Architecture (Целевая схема)

```text
User -> OpenClaw Agent -> turntable_* tools
                           |
                           v
                External OpenClaw Plugin (this repo)
                           |
                           v
            ai-hardware-controller HTTP API (:8000)
                           |
                           v
                     Turntable runtime/BLE
```

### Границы ответственности

- **OpenClaw Agent:** принимает пользовательскую задачу и выбирает tool.
- **External Plugin (this repo):** строго типизированный tool surface, safety policy, HTTP mapping, retry/timeout.
- **Turntable API/runtime (this repo):** исполнение команд и аппаратный контракт.

### Execution Model: Two Machines

- **Machine A (hardware/API host):** репозиторий `ai-hardware-controller`, BLE-доступ к turntable, подъем `turntable_tool_api` на `:8000`.
- **Machine B (OpenClaw host):** установка/настройка OpenClaw, загрузка внешнего plugin, allowlist tools, агентные сценарии.
- **Сетевой контракт:** Machine B должен иметь LAN-доступ к `http://<Machine-A-IP>:8000`.
- **Single source runbook:** `docs/references/openclaw-turntable-setup-runbook.md`.

### Operator Handoff Checklist (для нового человека)

- [ ] На Machine A проверен API (`/health`, `/state`) и зафиксирован актуальный `baseUrl`.
- [ ] На Machine B установлен OpenClaw и доступна команда `openclaw`.
- [ ] На Machine B plugin подключается из локального пути к этому репозиторию.
- [ ] На Machine B настроен allowlist для целевого агента.
- [ ] Выполнен минимальный сценарий: `state -> home -> move_to -> state -> return_base -> stop`.

### Contract Freeze Checklist (v1)

| Tool | HTTP endpoint | Success schema | Failure schema |
|---|---|---|---|
| `turntable_state` | `POST /state` | `{ ok: true, result: { rotation_deg, tilt_deg, status, ble_connected, zero_calibrated, reference_frame } }` | `{ ok: false, error: { code, message, http_status } }` |
| `turntable_home` | `POST /home` | `{ ok: true, result: { rotation_deg, tilt_deg, zero_calibrated, reference_frame } }` | `{ ok: false, error: { code, message, http_status } }` |
| `turntable_move_to` | `POST /move-to` | `{ ok: true, result: { executed, rotation_deg, tilt_deg, zero_calibrated, reference_frame } }` | `{ ok: false, error: { code, message, http_status } }` |
| `turntable_return_base` | `POST /return-base` | `{ ok: true, result: { mode, executed, rotation_deg, tilt_deg, zero_calibrated, reference_frame } }` | `{ ok: false, error: { code, message, http_status } }` |
| `turntable_stop` | `POST /stop` | `{ ok: true, result: { ack, status } }` | `{ ok: false, error: { code, message, http_status } }` |
| `turntable_commissioning_first_run` | `POST /commissioning/first-run` | `{ ok: true, result: { ready, summary, checks } }` | `{ ok: false, error: { code, message, http_status } }` |

### Safety Policy Matrix (v1 runtime policy)

| Trigger | Guard | Action | Escalation |
|---|---|---|---|
| Motion call requested | Pre-state check via `turntable_state` | If `status != IDLE`, reject motion | Return deterministic policy error |
| Side-effect tool call | `allowSideEffects == true` | If disabled, reject call | Operator enables allowlist/policy |
| Rapid repeated calls | `commandGapMs` anti-flood | Reject call in guard window | Agent must slow down call cadence |
| Duplicate `move_to` | `idempotencyWindowMs` | Skip deterministic duplicate move | Agent re-checks `state` before next action |
| Upstream/API ambiguity | transport/contract failure | Execute `turntable_stop` best-effort | Return structured escalation context |

### v1 Scope Freeze

- **In scope (v1):** external plugin package, config schema, tool registration, runtime safety guards, skill, docs/runbook/release notes.
- **Out of scope (v1):** high-frequency balancing loop, closed-loop servo control, OpenClaw core modifications, automatic physical calibration.

## 3. Execution Steps (Шаги выполнения)

### Phase A. План и freeze контракта

- [x] Шаг A1: Зафиксировать v1 контракт ручек и коды ошибок как source of truth (док + чеклист соответствия в плане). (2026-03-09 19:57)
  - **Deliverables:** таблица `tool -> endpoint -> expected success/error schema`.
- [x] Шаг A2: Зафиксировать safety policy как runtime policy (не только текст skill): pre-state, busy gate, stop-on-ambiguity, no parallel motion. (2026-03-09 19:57)
  - **Deliverables:** policy matrix (`trigger -> guard -> action -> escalation`).
- [x] Шаг A3: Зафиксировать scope v1 (обязательные ручки, optional commissioning, out-of-scope high-frequency balancing). (2026-03-09 19:57)
  - **Deliverables:** явный In/Out scope список и критерии переноса в backlog.
- [x] Шаг A4: Добавить phase gate для перехода к разработке plugin-кода. (2026-03-09 19:57)
  - **Критерий перехода:** A1-A3 отмечены, противоречий в контракте и policy не осталось.

### Phase B. Каркас внешнего plugin-пакета

- [x] Шаг B1: Создать пакет `integrations/openclaw-turntable-plugin/` с файлами: (2026-03-09 19:57)
  - `package.json`
  - `openclaw.plugin.json`
  - `index.ts`
  - `src/config.ts`
  - `src/client.ts`
  - `src/mappers.ts`
  - `skills/turntable/SKILL.md`
- [x] Шаг B2: Добавить `openclaw.plugin.json` с `id`, `configSchema`, `uiHints`. (2026-03-09 19:57)
- [x] Шаг B3: Зарегистрировать tools: (2026-03-09 19:57)
  - `turntable_state`
  - `turntable_home`
  - `turntable_move_to`
  - `turntable_return_base`
  - `turntable_stop`
  - `turntable_commissioning_first_run` (optional)
- [x] Шаг B4: Обозначить side-effect tools как `optional` и подготовить allowlist-only включение. (2026-03-09 19:57)
- [x] Шаг B5: Добавить минимальный smoke entrypoint plugin без сетевых вызовов (health/config check). (2026-03-09 19:57)
  - **Критерий перехода:** plugin грузится OpenClaw без runtime-исключений.

### Phase C. Конфиг и управление окружением

- [x] Шаг C1: Вынести в plugin config: (2026-03-09 19:57)
  - `baseUrl` (default `http://192.168.31.97:8000`)
  - `timeoutMs`
  - `retry.maxAttempts`
  - `retry.backoffMs`
  - `safety.maxTiltDeg`
  - `safety.minRotateSpeed`
  - `safety.minTiltSpeed`
- [x] Шаг C2: Подготовить пример операторской настройки через `openclaw config set`. (2026-03-09 19:57)
- [x] Шаг C3: Добавить fallback policy: network/API error -> structured tool error без silent success. (2026-03-09 19:57)
- [x] Шаг C4: Добавить startup-валидацию конфига plugin (тип, диапазоны, обязательные поля). (2026-03-09 19:57)
  - **Критерий перехода:** неверный конфиг детерминированно отклоняется до первого tool-вызова.

### Phase D. Safety policy в коде plugin

- [x] Шаг D1: Перед motion-командой делать `turntable_state` pre-check. (2026-03-09 19:57)
- [x] Шаг D2: При `status != IDLE` не запускать motion, возвращать deterministic error. (2026-03-09 19:57)
- [x] Шаг D3: Валидировать входы и ranges до HTTP call. (2026-03-09 19:57)
- [x] Шаг D4: На ambiguous/failure path делать `turntable_stop` и возвращать эскалационный контекст. (2026-03-09 19:57)
- [x] Шаг D5: Добавить локальный anti-flood (простая rate guard/command gap для plugin уровня). (2026-03-09 19:57)
- [x] Шаг D6: Добавить deterministic idempotency guard для повторных `move_to` с теми же параметрами в коротком окне. (2026-03-09 19:57)
  - **Критерий перехода:** нет параллельного motion и нет бесконтрольных повторов команд.

### Phase E. Skill для агента

- [x] Шаг E1: Написать `skills/turntable/SKILL.md` с обязательным безопасным циклом: (2026-03-09 19:57)
  - `state -> (home once) -> move_to -> state`
  - on error/ambiguity -> `stop -> state -> decide`.
- [x] Шаг E2: Добавить таблицу обработки ошибок (`DEVICE_BUSY`, `MOVE_FAILED`, `STOP_FAILED`, `BLE_CONNECT_FAILED`). (2026-03-09 19:57)
- [x] Шаг E3: Ограничить поведение skill: no parallel motion, no command flooding, no speculative recovery loops. (2026-03-09 19:57)
- [x] Шаг E4: Добавить explicit stop-condition для длинных задач (когда агент обязан эскалировать человеку). (2026-03-09 19:57)
  - **Критерий перехода:** skill-поток однозначен и не допускает unsafe self-retry циклов.

### Phase F. Интеграция с OpenClaw (без core правок)

- [ ] Шаг F1: Подключить plugin через `openclaw plugins install -l <path>` или `plugins.load.paths`. (**Owner:** Machine B)
- [ ] Шаг F2: Включить plugin: `plugins.entries.turntable.enabled=true`. (**Owner:** Machine B)
- [ ] Шаг F3: Включить tools только нужному агенту через `agents.list[].tools.allow`. (**Owner:** Machine B)
- [ ] Шаг F4: Проверить, что инструменты доступны агенту и недоступны там, где не разрешены. (**Owner:** Machine B)
- [x] Шаг F5: Зафиксировать операционный профиль включения (dev/staging/prod-like) и rollback-последовательность. (2026-03-09 19:57)
  - **Критерий перехода:** plugin можно отключить без влияния на остальные агенты/инструменты.

### Phase G. Тестирование

- [ ] Шаг G1: Unit tests plugin client/mappers/config parsing. (**Owner:** Machine B / Node env)
- [ ] Шаг G2: Contract tests tool response schema (`ok/result` vs `ok/error`) и mapping http-status -> tool errors. (**Owner:** Machine B / Node env)
- [ ] Шаг G3: Smoke tests без железа:
  - `scripts/turntable_tool_adapter_smoke.py`
  - `scripts/turntable_tool_api_smoke.py`
  - plugin mock-upstream smoke.
-  - **Owner split:** API/adapter smoke на Machine A (Python env), plugin smoke на Machine B (Node env).
- [ ] Шаг G4: Hardware acceptance:
  - `state -> home -> move-to -> state -> return-base -> stop`
  - commissioning endpoint
  - busy/failure behavior.
  - **Owner split:** выполнение команд из Machine B, физическое наблюдение и API health на Machine A.
- [ ] Шаг G5: Agent E2E сценарии (3-5 пользовательских задач) с проверкой safety policy.
- [x] Шаг G6: Прогнать `bash scripts/verify.sh`. (2026-03-09 19:57)
- [ ] Шаг G7: Прогнать негативные сценарии API недоступности/timeout и подтвердить корректный escalation JSON. (**Owner:** обе машины)
- [x] Шаг G8: Зафиксировать тест-отчет (что пройдено, что отложено) и связать с DoD. (2026-03-09 19:57)

> Примечание: тестовые файлы для G1/G2/G7 добавлены в пакет plugin, но не исполнены в текущем окружении из-за отсутствия `npm`.
> Примечание: для G3 `turntable_tool_adapter_smoke.py` пройден, но `turntable_tool_api_smoke.py` не запускается без Python-зависимостей (`fastapi`).

### Phase H. Документация и handoff

- [x] Шаг H1: Обновить `README.md` разделом "OpenClaw external plugin integration". (2026-03-09 19:57)
- [x] Шаг H2: Добавить runbook "оператор при аварии" (forced stop, escalation path, manual recovery). (2026-03-09 19:57)
- [x] Шаг H3: Зафиксировать Known Limitations и explicit out-of-scope. (2026-03-09 19:57)
- [x] Шаг H4: Подготовить "switch checklist" для запуска следующего агента. (2026-03-09 19:57)
- [x] Шаг H5: Обновить индекс справочников при добавлении новых docs (`docs/references/index.md`, при необходимости `docs/index.md`). (2026-03-09 19:57)
- [x] Шаг H6: Подготовить release notes v1 для plugin-интеграции (конфиг, ручки, ограничения). (2026-03-09 19:57)

> При выполнении шага: `- [x] Шаг ... (YYYY-MM-DD HH:MM)`
> После каждого выполненного шага — микро-коммит по Commit Harness.

## 4. Validation Matrix (Как будем тестировать)

### 4.1 Functional

- Tool registration корректна.
- Каждый tool вызывает корректную API ручку.
- Параметры и схемы совпадают с контрактом.

### 4.2 Safety

- Motion блокируется при non-IDLE.
- На ambiguous path вызывается `stop`.
- Нет параллельных motion операций.
- Ограничения tilt/speed enforced до отправки в API.

### 4.3 Reliability

- Timeout и retry работают предсказуемо.
- Ошибки сети не дают ложных `ok=true`.
- Reconnect/commissioning path не ломают контракт.

### 4.4 Agent Behavior

- Агент следует циклу из skill.
- Не спамит команды.
- Корректно эскалирует тяжелые ошибки.

### 4.5 Configuration Safety

- Некорректный `baseUrl` детектится до выполнения движения.
- Невалидные значения `timeout/retry/safety` отвергаются на startup.
- Side-effect tools недоступны без явного allowlist-включения.

### 4.6 Rollback Readiness

- Plugin можно отключить без правок OpenClaw core.
- При отключении plugin агент не получает "битые" tool registrations.
- Возврат к host-only runbook выполняется за один операторский шаг.

## 5. Definition of Done (Критерии готовности)

- [ ] Внешний plugin-пакет реализован и подключается без правок OpenClaw core.
- [ ] Все v1 tools доступны агенту через allowlist policy.
- [ ] Endpoint `baseUrl` вынесен в конфиг и редактируется без правок кода.
- [ ] Safety policy реализована в plugin runtime, не только в документации.
- [ ] Skill для turntable активен и отражает контракт эксплуатации.
- [ ] Пройдены smoke + contract + hardware acceptance + `scripts/verify.sh`.
- [ ] Документация и runbook достаточны для передачи задачи следующему агенту.
- [ ] Подготовлен rollback и проверено безопасное отключение plugin без побочных эффектов.
- [ ] Зафиксирован итоговый test-report с coverage по функционалу/safety/reliability.

## 6.1 Phase Gates (Go/No-Go)

- **Gate A -> B:** контракт и safety policy заморожены, scope v1 согласован.
- **Gate C -> D:** конфиг валидируется до runtime-вызовов, fallback policy подтверждена.
- **Gate F -> G:** tools корректно видимы только в разрешенных агентах (allowlist enforced).
- **Gate G -> H:** тесты и verify прошли, нерешенные риски явно вынесены в tech debt.

## 6. Surprises & Discoveries (Сюрпризы и находки)

- Пока пусто. Заполнять по факту в формате:
  - **(YYYY-MM-DD HH:MM) Сюрприз:** ...
    - **Контекст:** ...
    - **Решение:** ...
    - **Harness Update:** ...
- **(2026-03-09 19:57) Сюрприз:** в окружении отсутствует `npm`, поэтому Node-based plugin tests/build не запускаются локально.
  - **Контекст:** попытка выполнить `npm install` в `integrations/openclaw-turntable-plugin`.
  - **Решение:** добавлены тесты и smoke entrypoint в репозиторий, но их запуск вынесен в шаг post-setup (после установки Node/npm).
  - **Harness Update:** тест-статус и ограничения зафиксированы в `docs/references/openclaw-turntable-plugin-test-report-v1.md`.
- **(2026-03-09 19:57) Сюрприз:** в окружении есть `python3`, но отсутствует `pip`, поэтому нельзя установить `fastapi` для `turntable_tool_api_smoke.py`.
  - **Контекст:** попытка запуска smoke-скриптов API после добавления plugin-слоя.
  - **Решение:** зафиксировать блокер окружения и оставить API smoke в статусе pending до установки Python-зависимостей.
  - **Harness Update:** отчет обновлен в `docs/references/openclaw-turntable-plugin-test-report-v1.md`.

## 7. Decision Trace (Журнал решений)

| Решение | Альтернативы | Почему выбрано | Дата |
|---|---|---|---|
| Интеграция через внешний plugin в этом репо | Изменять OpenClaw core | Минимальный риск, чистая ответственность, быстрые итерации | 2026-03-09 |
| Конфигурируемый `baseUrl` (default LAN) | Жесткий хардкод endpoint | Безопасная эксплуатация и удобство переноса между стендами | 2026-03-09 |
| Safety в коде plugin + skill | Только skill/промпт | Защита от ошибочных LLM-решений на уровне исполнения | 2026-03-09 |
| Side-effect tools по умолчанию выключены | Включать все tools всегда | Снижает риск несанкционированных движений и принуждает allowlist-модель | 2026-03-09 |
| Внедрены anti-flood и idempotency guards в plugin | Полагаться только на runtime/устройство | Дополнительная защита от command flooding и дублирования движения на plugin-уровне | 2026-03-09 |

## 8. Leftover Tech Debt (Оставшийся технический долг)

- [ ] Добавить нагрузочные тесты длительной серии motion-команд.
- [ ] Добавить автоматический анализ JSONL-телеметрии с anomaly flags.
- [ ] Описать процедуру обновления plugin версии и обратной совместимости контрактов.
- [ ] Добавить chaos-сценарии нестабильной сети для проверки retry/backoff политики plugin.

## 9. Switch Checklist (для следующего агента)

Перед началом реализации:

1. Прочитать `AGENTS.md` и `docs/index.md`.
2. Взять этот план в работу (`Status: In Progress`, проставить branch).
3. Работать по шагам Phase A -> H, отмечая чекбоксы и коммитя по триггерам.
4. Каждый сюрприз фиксировать в секции `Surprises & Discoveries`.
5. Перед handoff запускать `bash scripts/verify.sh`.
6. Сначала согласовать роли по двум машинам:
   - Machine A: API/BLE operator;
   - Machine B: OpenClaw/plugin operator.
7. Идти по `docs/references/openclaw-turntable-setup-runbook.md` шаг за шагом без пропуска acceptance checklist.


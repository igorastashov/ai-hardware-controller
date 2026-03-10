# OpenClaw Turntable Operator Workflow

## Purpose
Практическая инструкция для ежедневной работы оператором на Machine B: запуск агента, управление чатом, безопасные команды и обработка типовых сбоев.

## Current limitation (2026.3.8)

На OpenClaw `2026.3.8` легко поймать ложный "runtime-блокер": plugin `turntable` загружен, но `turntable_*` tools не попадают в toolset агента (`Tool turntable_state not found`) при конфигурации `tools.profile="minimal"` + plugin-only `tools.allow`.

Рабочий фикс:
- использовать `tools.alsoAllow` для `turntable_*` (а не `tools.allow`), сохраняя `tools.profile="minimal"`;
- перезапустить gateway и повторить agent one-shot проверку.

Если после этого проблема сохраняется, используйте fallback-модель:
- Machine A: выполнять команды управления turntable через HTTP API/CLI.
- Machine B: использовать OpenClaw агент как операторский ассистент (сценарии, интерпретация JSON-ответов, протокол безопасности), а не как прямой исполнитель `turntable_*`.

## 0) Preflight (каждый старт смены)

```bash
source ~/.bashrc
openclaw --version
openclaw gateway status
openclaw plugins info turntable
curl -sS "http://192.168.31.97:8000/health"
curl -sS -X POST "http://192.168.31.97:8000/state"
```

Ожидание:
- Gateway `running` и `RPC probe: ok`.
- Plugin `turntable` в статусе `loaded`.
- API на Machine A отвечает `ok: true`.

## 0.1) Production tool policy (обязательно)

Чтобы агент не уходил в локальные shell/python сценарии, зафиксируйте профиль инструментов для `main`:

```bash
openclaw config set agents.list[0].id "main"
openclaw config set agents.list[0].tools.profile "minimal"
openclaw config unset agents.list[0].tools.allow
openclaw config set agents.list[0].tools.alsoAllow '[
  "turntable_state",
  "turntable_home",
  "turntable_move_to",
  "turntable_return_base",
  "turntable_stop",
  "turntable_commissioning_first_run"
]'
openclaw config set agents.list[0].tools.deny '["group:runtime","group:fs"]'
openclaw gateway restart
```

Проверка:

```bash
openclaw config get agents.list[0].tools
```

Должны быть:
- `profile: "minimal"`
- `alsoAllow: ["turntable_*"...]`
- `deny: ["group:runtime","group:fs"]`

## 1) Запуск рабочего сеанса

Интерактивный режим (основной):

```bash
openclaw tui --session main --deliver
```

One-shot режим (для быстрых проверок):

```bash
openclaw agent --agent main --session-id main --message "Проверь состояние turntable и верни JSON"
```

Fallback one-shot (если `turntable_*` не доступны агенту):

```bash
curl -sS -X POST "http://192.168.31.97:8000/state"
openclaw agent --agent main --session-id main --message "Проанализируй этот JSON состояния turntable и дай безопасный следующий шаг: <PASTE_JSON>"
```

## 1.1) Быстрый старт для нового терминала (30 секунд)

```bash
source ~/.bashrc
openclaw --version
openclaw plugins info turntable
openclaw gateway restart
openclaw tui --session main --deliver
```

Если `openclaw` не найден:

```bash
/home/<user>/.npm-global/bin/openclaw --version
```

## 2) Базовый протокол общения с агентом

Используйте формулировки, которые явно требуют tool-вызов:

- `Используй только tool turntable_state. Не запускай shell/python. Верни сырой JSON ответа tool.`
- `Сделай turntable_home один раз, затем turntable_state. Верни оба JSON-ответа.`
- `Выполни turntable_move_to rotation=30 tilt=10, затем turntable_state.`
- `Если статус не IDLE или есть ошибка, выполни turntable_stop и верни JSON.`

Для надежности добавляйте ограничения:
- `Не делай предположений.`
- `Не используй fallback через локальные скрипты.`
- `Отвечай только результатом tool-вызовов.`

## 3) Рекомендованный безопасный сценарий

1. `turntable_state` (pre-check).
2. `turntable_home` (один раз в начале сессии при необходимости).
3. `turntable_move_to` (малые шаги, без параллельных команд).
4. `turntable_state` (post-check).
5. `turntable_return_base` или `turntable_stop` по ситуации.

## 4) Управление сессией

- Одна активная операторская сессия: `main`.
- Если контекст "зашумился", откройте новый TUI-сеанс и дайте короткий bootstrap-промпт с правилами tool-only.
- Для диагностик используйте отдельные one-shot команды, не смешивайте с рабочим диалогом.

## 5) Типовые сбои и быстрые действия

### `openclaw: command not found`

```bash
source ~/.bashrc
openclaw --version
```

Или вызывайте бинарник напрямую:

```bash
/home/<user>/.npm-global/bin/openclaw --version
```

### Агент пишет про `bleak`/локальные скрипты вместо `turntable_*`

Это обычно промпт-дрейф, а не поломка plugin.

Действия:
1. Повторите запрос в формате `tool-only`.
2. Убедитесь, что allowlist на агенте `main` настроен.
3. Перезапустите gateway:
   `openclaw gateway restart`

### `Tool not available`

Проверьте:
- `plugins.entries.turntable.enabled=true`
- `agents.list[0].id="main"`
- `agents.list[0].tools.alsoAllow` содержит `turntable_*`
- `openclaw plugins info turntable` показывает `Status: loaded`

Если всё выше в норме, но агент всё равно отвечает `Tool ... not found`, переключайтесь в fallback-режим (HTTP API + ассистентный анализ) и зафиксируйте кейс как upstream issue.

## 6) Минимальный end-of-shift checklist

- Последняя проверка `turntable_state` успешна.
- Нет активного движения (`status=IDLE`).
- Зафиксированы необычные события/ошибки.
- Gateway и plugin остаются в рабочем состоянии.

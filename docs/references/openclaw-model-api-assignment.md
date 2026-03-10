# OpenClaw Model/API Assignment Guide

## Purpose

Единая точка для назначения и пересмотра провайдеров/моделей/API под разные задачи:
- текстовые LLM;
- VLM (vision-language);
- аудио API (STT/TTS);
- будущие мультимодальные и специализированные маршруты.

Документ живой: дополняется по мере появления новых провайдеров, моделей и сценариев.

## Scope

Этот файл отвечает за:
- какие модели и API считаются "рабочими по умолчанию";
- где и как их переключать в OpenClaw;
- какие ограничения/риски известны;
- какой fallback использовать при деградации провайдера.

Этот файл не заменяет продуктовые требования и не описывает бизнес-логику turntable.

## Assignment Registry

> Обновляй таблицу при каждом изменении назначений.

| Capability | Provider/API | Model/Endpoint | Environment | Status | Notes |
|---|---|---|---|---|---|
| Text LLM (agent default) | TBD | TBD | dev | Draft | Заполнить после фикса целевого профиля |
| Vision (VLM) | TBD | TBD | dev | Backlog | Добавить после подтверждения формата входных изображений |
| Audio STT | TBD | TBD | dev | Backlog | Добавить после выбора языка/latency требований |
| Audio TTS | TBD | TBD | dev | Backlog | Добавить после выбора voice policy |

## Quick Switch Playbook

### 1) Принцип переключения

- Сначала проверяем, что провайдер авторизован.
- Затем меняем модель (session-level или persistent-level).
- Затем перезапускаем gateway.
- После перезапуска делаем короткий smoke-запрос.
- Только после успешного smoke считаем переключение примененным.

### 2) Быстрое переключение в текущей сессии (без изменения дефолта)

Используйте в `openclaw tui`:

```text
/model list
/model <provider/model>
/model status
```

Пример:

```text
/model openrouter/anthropic/claude-sonnet-4-5
```

### 3) Переключение по умолчанию (persistent)

```bash
openclaw models list
openclaw models set <provider/model>
openclaw models status
openclaw gateway restart
```

Пример:

```bash
openclaw models set openrouter/google/gemini-2.0-flash-001
openclaw models status
openclaw gateway restart
```

### 4) Смена провайдера (auth + model)

#### OpenRouter

```bash
openclaw onboard --auth-choice apiKey --token-provider openrouter --token "$OPENROUTER_API_KEY"
openclaw models set openrouter/anthropic/claude-sonnet-4-5
openclaw models status
```

#### OpenAI

```bash
openclaw onboard --auth-choice openai-api-key
openclaw models set openai/gpt-5.4
openclaw models status
```

#### Anthropic

```bash
openclaw models auth paste-token --provider anthropic
openclaw models set anthropic/claude-opus-4-6
openclaw models status
```

### 5) Минимальный smoke-check

```bash
openclaw --version
openclaw gateway status
openclaw gateway restart
openclaw agent --agent main --session-id main --message "Проверь доступность инструментов и ответь коротко."
```

### 6) Fallback policy

- При нестабильности нового провайдера возвращаем предыдущее рабочее назначение.
- Инцидент фиксируем в секции `Change Log` этого документа.
- Если поломка повторяется, добавляем отдельную заметку в `Known Issues`.

## Configuration Mapping (template)

Заполняется при фиксации рабочего конфига:

| Config path | Value | Why |
|---|---|---|
| `models.providers.<id>` | TBD | Провайдер и ключи |
| `agents.defaults.model.primary` | TBD | Дефолтная модель |
| `agents.defaults.model.fallbacks[]` | TBD | Цепочка fallback |
| `agents.list[].model` (если используется) | TBD | Переопределение для конкретного агента |
| `agents.defaults.models` (если используется) | TBD | Allowlist/каталог разрешенных моделей |

## Known Issues

- Пока пусто.

## Change Log

| Date | Change | Author | Verification |
|---|---|---|---|
| 2026-03-10 | Создан базовый документ для назначения model/API | Cursor Agent | N/A |
| 2026-03-10 | Добавлены команды quick switch: `/model`, `openclaw models set`, auth flow для смены провайдера | Cursor Agent | Команды сверены по docs OpenClaw (`concepts/models`, `providers/openrouter`, `concepts/model-providers`) |

## Culture of Maintenance (обязательные правила ведения)

1. **Один факт — одна запись.** Любое изменение назначения модели/API фиксируется в `Change Log`.
2. **Сначала проверка, потом объявление.** Новое назначение считается валидным только после smoke-check.
3. **Пиши причины, а не только значения.** В `Assignment Registry` и `Configuration Mapping` указывай "почему выбрано".
4. **Не удаляй историю решений.** Старые строки не стираем; помечаем статусом (`Deprecated`, `Replaced`, `Blocked`).
5. **Минимизируй "магический конфиг".** Любой нестандартный параметр должен иметь короткое объяснение.
6. **Расширяй, не ломая структуру.** Для новых классов API (VLM/audio/realtime) добавляй строки в реестр и секции issue/fallback, а не переписывай документ заново.


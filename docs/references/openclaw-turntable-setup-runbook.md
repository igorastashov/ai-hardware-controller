# OpenClaw + Turntable Setup Runbook

## Purpose

Пошаговая инструкция для оператора:

1. Развернуть и настроить OpenClaw.
2. Поднять API из этого репозитория (`ai-hardware-controller`).
3. Подключить внешний turntable plugin к OpenClaw.
4. Управлять физическим железом через агента из терминала.

## Target architecture

```text
Terminal User
  -> OpenClaw Agent (CLI/TUI)
    -> turntable_* tools (external plugin)
      -> ai-hardware-controller HTTP API (http://192.168.31.97:8000)
        -> BLE runtime
          -> Physical turntable
```

## Prerequisites

- Хост с OpenClaw и Node 22+.
- Этот репозиторий (`ai-hardware-controller`) с рабочими Python-зависимостями.
- Доступ к устройству по BLE.
- LAN-доступ OpenClaw-хоста к `192.168.31.97`.

## Two-machine operating model (recommended)

### Machine A (hardware/API host)
- Здесь находится turntable и BLE-доступ.
- Здесь запускается `ai-hardware-controller` API (`scripts/run_turntable_host_api.sh`).
- Здесь подтверждается физическое поведение стола.

### Machine B (OpenClaw host)
- Здесь установлен OpenClaw и запускается агент (`openclaw tui` / `openclaw agent`).
- Здесь ставится и настраивается внешний plugin.
- Здесь ведется операторская работа с tool allowlist и сценариями агента.

### Cross-machine handoff data (must share)
- Актуальный `baseUrl` (пример: `http://192.168.31.97:8000`).
- BLE address устройства.
- Версия plugin/ветка репозитория.
- Статус последнего acceptance прогона.

---

## Step 1. Install OpenClaw

Рекомендуемый способ:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

Альтернатива через npm:

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

Проверка:

```bash
openclaw --version
openclaw doctor
```

Если `openclaw: command not found` в новом терминале:

```bash
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
openclaw --version
```

Вне зависимости от PATH всегда можно вызвать бинарник напрямую:

```bash
/home/<user>/.npm-global/bin/openclaw --version
```

---

## Step 2. Initial OpenClaw onboarding

Запустите базовую настройку:

```bash
openclaw onboard --install-daemon
```

Проверьте Gateway:

```bash
openclaw gateway status
openclaw status
```

Если нужно, перезапустите:

```bash
openclaw gateway restart
```

---

## Step 3. Start ai-hardware-controller API

### Recommended (host Python process)

Из корня `ai-hardware-controller`:

```bash
py -3 -m pip install -r requirements.txt
bash scripts/run_turntable_host_api.sh D3:36:39:34:5D:29 0.0.0.0 8000
```

### Docker mode (proxy to host API)

```bash
docker compose up -d --build
docker compose ps
```

Проверка API:

```bash
curl -sS "http://192.168.31.97:8000/health"
curl -sS -X POST "http://192.168.31.97:8000/state"
```

> Этот шаг выполняется на **Machine A**.

---

## Step 4. Install external turntable plugin into OpenClaw

> Этот шаг предполагает, что plugin уже реализован по плану:
> `docs/exec-plans/active/openclaw-turntable-external-plugin-integration.md`

Пример установки plugin через link:

```bash
openclaw plugins install -l /ABS/PATH/TO/ai-hardware-controller/integrations/openclaw-turntable-plugin
openclaw plugins list
```

Включение plugin:

```bash
openclaw config set plugins.entries.turntable.enabled true
```

Настройка endpoint:

```bash
openclaw config set plugins.entries.turntable.config.baseUrl "http://192.168.31.97:8000"
```

Рекомендуется также выставить timeout/retry в `plugins.entries.turntable.config.*`.

> Этот шаг выполняется на **Machine B**.

---

## Step 5. Allow turntable tools for target agent

Вариант через конфиг-файл (`~/.openclaw/openclaw.json`), пример:

```json5
{
  agents: {
    list: [
      {
        id: "main",
        tools: {
          allow: [
            "turntable_state",
            "turntable_home",
            "turntable_move_to",
            "turntable_return_base",
            "turntable_stop",
            "turntable_commissioning_first_run",
          ],
        },
      },
    ],
  },
}
```

После изменения конфига:

```bash
openclaw gateway restart
openclaw plugins info turntable
```

CLI-вариант (рекомендуется для Linux onboarding), если `agents.list` еще пуст:

```bash
openclaw config set agents.list[0].id "main"
openclaw config set agents.list[0].tools.profile "minimal"
openclaw config set agents.list[0].tools.allow '[
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

> Этот шаг выполняется на **Machine B**.

---

## Step 6. Talk to agent from terminal

### Interactive terminal mode (recommended)

```bash
openclaw tui --session main --deliver
```

### One-shot terminal command

```bash
openclaw agent --agent main --session-id main --message "Проверь состояние turntable и дай краткий отчет"
```

> Этот шаг выполняется на **Machine B**, при этом API должен быть активен на **Machine A**.

---

## Step 7. Safe command sequence (operator prompts)

После подключения tools используйте команды в таком стиле:

1. `Проверь состояние стола (turntable_state).`
2. `Если нужно, сделай home один раз и подтверди reference frame.`
3. `Перемести в rotation 30, tilt 10 и затем повторно проверь state.`
4. `Если статус нештатный, выполни stop и сообщи код ошибки.`

Ожидаемая safety-политика:

- всегда pre-check через `turntable_state`;
- не запускать новую motion-команду при non-IDLE;
- при неоднозначности выполнять `turntable_stop`.

---

## Step 8. Acceptance checklist

- OpenClaw запущен и отвечает (`openclaw status`).
- API отвечает на `health` и `state`.
- Plugin установлен и включен.
- `baseUrl` указывает на `http://192.168.31.97:8000`.
- Агент из `openclaw tui` успешно вызывает `turntable_state`.
- Базовый сценарий `home -> move_to -> state -> return_base -> stop` проходит.

## Human handoff checklist (new operator)

- Получены данные доступа и версия репозитория/plugin.
- Подтверждено, какая машина является Machine A и какая Machine B.
- На Machine A подтвержден живой API.
- На Machine B подтвержден plugin load + enabled + allowlist.
- Пройден минимум `state -> move_to small -> state -> stop`.

---

## Troubleshooting

- `Tool not available`: проверь `plugins.entries.turntable.enabled` и allowlist tools.
- `Connection refused` к `:8000`: проверь, что API реально поднят и слушает LAN-интерфейс.
- `BLE_CONNECT_FAILED`: перепроверь адрес устройства и host-run API path.
- Долгие таймауты: увеличь `timeoutMs` в plugin config и сократи частоту motion-команд.
- `openclaw: command not found`: выполни `source ~/.bashrc` или используй абсолютный путь `/home/<user>/.npm-global/bin/openclaw`.
- `Tool turntable_state not found` при `plugins info turntable = loaded`: это известный runtime-блокер OpenClaw `2026.3.8`; переходите в fallback-режим (HTTP API/CLI + ассистентный анализ в агенте), см. `docs/references/openclaw-turntable-operator-workflow.md`.


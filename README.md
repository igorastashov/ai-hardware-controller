# AI Hardware Controller

Репозиторий с универсальным AI-Native каркасом для ведения проектов с участием автономных агентов и людей.

## Быстрый старт

```bash
# Клонирование
git clone <url> && cd ai-hardware-controller

# Установка Python-зависимостей
py -3 -m pip install -r requirements.txt

# Проверка целостности проекта
bash scripts/verify.sh
```

Для Windows/PowerShell используйте:

```powershell
powershell -File scripts/verify.ps1
```

## Запуск API через Docker Compose

```powershell
# Опционально: задать адрес устройства
$env:TURNTABLE_ADDRESS="D3:36:39:34:5D:29"

# Сборка и запуск сервиса
docker compose up -d --build

# Проверка статуса
docker compose ps
```

> Для Docker Desktop на Windows BLE из контейнера может быть недоступен. Для физического управления и first-run приемки запускайте `scripts/turntable_commissioning.py` в host Python окружении.

Для доступа OpenClaw к host API:

```bash
bash scripts/run_turntable_host_api.sh D3:36:39:34:5D:29 127.0.0.1 18000
docker compose up -d --build
```

- OpenClaw в контейнере на этом же ПК: `http://host.docker.internal:8000`
- OpenClaw на другом ПК в локальной сети: `http://192.168.31.97:8000` (проверьте актуальный IPv4 через `ipconfig`)

## Документация

Полная документация, структура проекта и правила работы описаны в [`docs/index.md`](docs/index.md).

Если вы новый участник проекта — начните с этого файла. Он содержит карту всех папок, инструкции по ведению документации и правила расширения каркаса.

## Для AI-агентов

Точка входа для автономных агентов — [`AGENTS.md`](AGENTS.md).

## OpenClaw external plugin integration

Внешний plugin для OpenClaw находится в `integrations/openclaw-turntable-plugin`.

Что дает plugin:
- tool-surface `turntable_state/home/move_to/return_base/stop/commissioning_first_run`;
- safety-policy в runtime plugin (pre-state check, anti-flood, idempotency guard, stop on ambiguity);
- конфигурируемый `baseUrl`, timeout/retry и side-effect gating.

Быстрый цикл разработки plugin:

```bash
cd integrations/openclaw-turntable-plugin
npm install
npm run test
npm run build
npm run smoke
```

Подробный план интеграции: `docs/exec-plans/active/openclaw-turntable-external-plugin-integration.md`.

## Лицензия

Apache License 2.0 — см. [LICENSE](LICENSE).

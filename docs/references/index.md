# Каталог справочных материалов (References)

> Шпаргалки по стеку, библиотекам и инструментам, используемым в проекте.
> Нужны для того, чтобы агенты не «галлюцинировали» про API и конфигурации.

## Когда добавлять шпаргалку

- Когда агент **повторно** ошибается в использовании конкретной технологии.
- Когда библиотека имеет неочевидный API или нюансы конфигурации.
- Когда появился новый инструмент в стеке проекта.

**НЕ** добавляй шпаргалки «на всякий случай». Добавляй только по факту реальной проблемы.

## Рекомендуемый формат файла

```markdown
# [Название технологии / библиотеки]

## Версия
x.y.z

## Особенности использования в этом проекте
- Мы используем библиотеку так: ...
- Мы НЕ используем фичу X, потому что: ...

## Типичные паттерны (примеры кода)
...

## Известные подводные камни
- Проблема: ...
  Решение: ...
```

## Реестр

| # | Файл | Технология | Описание |
|---|---|---|---|
| 1 | `docs/references/revopoint-dual-axis-turntable.md` | Revopoint Dual-axis Turntable (BLE) | Профиль устройства, лимиты осей, lifecycle confidence и правила движения для будущего драйвера/agent tools |
| 2 | `docs/references/turntable-tool-cli-runbook.md` | Turntable Tool CLI | Пошаговый операторский runbook для ручек `state/home/move-to/stop` |
| 3 | `docs/references/openclaw-turntable-agent-instruction.md` | OpenClaw Agent Guidance | Инструкция агенту по безопасному циклу вызова turntable-ручек и обработке ошибок |
| 4 | `docs/references/openclaw-turntable-tool-contract.md` | OpenClaw Tool Contract | Формальный перечень ручек, ограничений, ошибок и политики вызовов |
| 5 | `docs/references/openclaw-turntable-test-plan.md` | OpenClaw Test Plan | План тестирования инфраструктуры ручек, probe-проверок и критериев приемки |
| 6 | `docs/references/openclaw-turntable-future-agent-work.md` | OpenClaw Agent Backlog | Бэклог задач будущего агента для финальной интеграции и эксплуатации |
| 7 | `docs/references/openclaw-turntable-operator-emergency-runbook.md` | OpenClaw Operator Emergency Runbook | Процедура аварийной остановки, эскалации и rollback в host-only режим |
| 8 | `docs/references/openclaw-turntable-plugin-release-notes-v1.md` | OpenClaw Plugin Release Notes | Итог v1 интеграции: состав фич, ограничения и эксплуатационные заметки |
| 9 | `docs/references/openclaw-turntable-plugin-integration-guide.md` | OpenClaw Plugin Integration Guide | Пошаговое подключение plugin, конфиг, allowlist policy и rollback |
| 10 | `docs/references/openclaw-turntable-plugin-test-report-v1.md` | OpenClaw Plugin Test Report | Сводка покрытия и ограничений тестирования в текущем окружении |
| 11 | `docs/references/openclaw-turntable-setup-runbook.md` | OpenClaw + Turntable Setup Runbook | Операторский путь от установки OpenClaw до вызова turntable tools из терминала |

---

> **Как добавить:** Создай файл `docs/references/<технология>.md`. Добавь строку в таблицу выше.

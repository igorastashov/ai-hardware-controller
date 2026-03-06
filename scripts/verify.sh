#!/usr/bin/env bash
set -euo pipefail

# Engineering Harness: главный скрипт валидации.
# Контракт: см. scripts/index.md
#
# Этот файл входит в иммутабельное ядро репозитория.
# Расширяй его по мере роста проекта, но не удаляй.

echo "=== verify.sh: Запуск проверок ==="

ERRORS=0

# --- Секция 1: Проверка структуры каркаса ---
echo ""
echo "[1/3] Проверка иммутабельных файлов каркаса..."

REQUIRED_FILES=(
  "AGENTS.md"
  "README.md"
  "ARCHITECTURE.md"
  "docs/index.md"
  "docs/design-docs/core-beliefs.md"
  "docs/design-docs/index.md"
  "docs/exec-plans/TEMPLATE.md"
  "docs/exec-plans/tech-debt-tracker.md"
  "docs/product-specs/index.md"
  "docs/references/index.md"
  "scripts/index.md"
  "scripts/verify.sh"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "  ОШИБКА: Отсутствует обязательный файл: $f"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ $ERRORS -eq 0 ]; then
  echo "  OK: Все файлы каркаса на месте."
fi

# --- Секция 2: Линтинг (заглушка) ---
echo ""
echo "[2/3] Линтинг..."
echo "  ПРОПУСК: Линтер не настроен. Добавь проверки при выборе стека."

# --- Секция 3: Тесты (заглушка) ---
echo ""
echo "[3/3] Тесты..."
echo "  ПРОПУСК: Тесты не настроены. Добавь проверки при появлении кода."

# --- Итог ---
echo ""
if [ $ERRORS -gt 0 ]; then
  echo "=== ПРОВАЛ: Найдено ошибок: $ERRORS ==="
  exit 1
else
  echo "=== УСПЕХ: Все проверки пройдены ==="
  exit 0
fi

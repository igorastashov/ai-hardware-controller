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
echo "[1/4] Проверка иммутабельных файлов каркаса..."

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

# --- Секция 2: Синхронность критичных правил в документации ---
echo ""
echo "[2/4] Проверка синхронности BLOCKER-правил..."
PYTHON_CMD=()
if command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
  PYTHON_CMD=(python)
elif command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
  PYTHON_CMD=(python3)
elif command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
  PYTHON_CMD=(py -3)
else
  echo "  ОШИБКА: Не найден Python интерпретатор (python/python3/py)."
  ERRORS=$((ERRORS + 1))
fi

if [ ${#PYTHON_CMD[@]} -gt 0 ] && "${PYTHON_CMD[@]}" scripts/check_docs_blockers_sync.py; then
  echo "  OK: Чеклисты критичных правил синхронизированы."
else
  if [ ${#PYTHON_CMD[@]} -gt 0 ]; then
    echo "  ОШИБКА: Несинхронизированные критичные правила в документации."
    ERRORS=$((ERRORS + 1))
  fi
fi

# --- Секция 3: Линтинг (заглушка) ---
echo ""
echo "[3/4] Линтинг..."
echo "  ПРОПУСК: Линтер не настроен. Добавь проверки при выборе стека."

# --- Секция 4: Тесты (заглушка) ---
echo ""
echo "[4/4] Тесты..."
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

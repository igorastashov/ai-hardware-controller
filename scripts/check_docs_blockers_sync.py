#!/usr/bin/env python3
"""
Проверка синхронности критичных правил в AGENTS.md и repo-conventions.mdc.

Контракт:
- Exit code 0: критичные маркеры и чеклисты синхронизированы.
- Exit code 1: найдено расхождение.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parent.parent
AGENTS_FILE = ROOT / "AGENTS.md"
RULES_FILE = ROOT / ".cursor" / "rules" / "repo-conventions.mdc"

AGENTS_CHECKLIST_HEADING = "## Протокол первого ответа (обязателен)"
RULES_CHECKLIST_HEADING = "### Обязательный чеклист первого подтверждения"

# Масштабируемый реестр: при добавлении новых критичных правил
# достаточно расширить эти маркеры.
REQUIRED_RULE_IDS = [
    "commit harness",
    "docs first",
    "exec plan",
    "surprises",
    "verify before finish",
    "multi-agent",
    "immutable core",
]

# Каждый пункт чеклиста описывается маркерами.
# Пункт считается найденным, если в одном checklist item присутствуют все маркеры.
CHECKLIST_MARKERS = [
    ["commit harness"],
    ["docs first", "docs/index md"],
    ["exec plan", "surprises", "discoveries"],
    ["verify before finish", "scripts/verify sh"],
    ["multi-agent", "immutable", "core"],
]


def _normalize(text: str) -> str:
    lowered = text.strip().lower()
    lowered = lowered.replace("ё", "е")
    lowered = re.sub(r"`+", "", lowered)
    lowered = re.sub(r"[^a-zа-я0-9\s\-/]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _extract_checklist_items(content: str, heading: str) -> List[str]:
    lines = content.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return []

    items: List[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        if re.match(r"^- \[x\]\s+.+", stripped, flags=re.IGNORECASE):
            items.append(re.sub(r"^- \[x\]\s+", "", stripped, flags=re.IGNORECASE))
    return items


def _validate_checklist_items(items: List[str], file_path: str) -> List[dict]:
    issues: List[dict] = []
    normalized_items = [_normalize(item) for item in items]

    if len(normalized_items) < len(CHECKLIST_MARKERS):
        issues.append(
            {
                "code": "CHECKLIST_TOO_SHORT",
                "file": file_path,
                "items_count": len(normalized_items),
                "required_min_count": len(CHECKLIST_MARKERS),
                "message": "Чеклист содержит меньше пунктов, чем требуется.",
            }
        )

    for marker_set in CHECKLIST_MARKERS:
        matched = any(all(marker in item for marker in marker_set) for item in normalized_items)
        if not matched:
            issues.append(
                {
                    "code": "CHECKLIST_MARKER_MISSING",
                    "file": file_path,
                    "markers": marker_set,
                    "message": "Не найден обязательный пункт чеклиста по маркерам.",
                }
            )

    return issues


def _collect_issues() -> List[dict]:
    issues: List[dict] = []

    if not AGENTS_FILE.exists():
        issues.append(
            {
                "code": "MISSING_FILE",
                "file": str(AGENTS_FILE.relative_to(ROOT)),
                "message": "Отсутствует AGENTS.md",
            }
        )
        return issues

    if not RULES_FILE.exists():
        issues.append(
            {
                "code": "MISSING_FILE",
                "file": str(RULES_FILE.relative_to(ROOT)),
                "message": "Отсутствует repo-conventions.mdc",
            }
        )
        return issues

    agents_content = AGENTS_FILE.read_text(encoding="utf-8")
    rules_content = RULES_FILE.read_text(encoding="utf-8")

    agents_items = _extract_checklist_items(agents_content, AGENTS_CHECKLIST_HEADING)
    rules_items = _extract_checklist_items(rules_content, RULES_CHECKLIST_HEADING)

    if not agents_items:
        issues.append(
            {
                "code": "MISSING_CHECKLIST",
                "file": "AGENTS.md",
                "heading": AGENTS_CHECKLIST_HEADING,
                "message": "Не найден чеклист первого подтверждения.",
            }
        )

    if not rules_items:
        issues.append(
            {
                "code": "MISSING_CHECKLIST",
                "file": ".cursor/rules/repo-conventions.mdc",
                "heading": RULES_CHECKLIST_HEADING,
                "message": "Не найден чеклист первого подтверждения.",
            }
        )

    if issues:
        return issues

    issues.extend(_validate_checklist_items(agents_items, "AGENTS.md"))
    issues.extend(_validate_checklist_items(rules_items, ".cursor/rules/repo-conventions.mdc"))

    combined_text = f"{_normalize(agents_content)}\n{_normalize(rules_content)}"
    for rule_id in REQUIRED_RULE_IDS:
        if rule_id not in combined_text:
            issues.append(
                {
                    "code": "MISSING_REQUIRED_RULE_ID",
                    "rule_id": rule_id,
                    "message": "Критичный маркер отсутствует в наборе документов.",
                }
            )

    return issues


def main() -> int:
    issues = _collect_issues()
    if issues:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "check": "docs_blockers_sync",
                    "issues": issues,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "check": "docs_blockers_sync",
                "files": ["AGENTS.md", ".cursor/rules/repo-conventions.mdc"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

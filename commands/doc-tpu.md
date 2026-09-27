---
description: Генерация отчётного документа ТПУ (.docx, .pdf) из content.md и static.json
argument-hint: [путь к content.md]
allowed-tools: [Bash, Read, Write, Glob, Grep, AskUserQuestion]
---

# /doc-tpu — Генератор отчётных документов ТПУ

Генерирует отчётный документ ТПУ с титульной страницей, логотипом и форматированием по стандартам.

## Аргументы

Пользователь вызвал: $ARGUMENTS

## Инструкция

1. Если пользователь указал путь к content.md — используй его. Иначе создай `report/content.md` по данным из SKILL.md.
2. Загрузи скилл docTPU через Skill tool для получения полной инструкции.
3. Следуй workflow из скилла: создай папку report/, скопируй шаблон и логотип, собери данные у пользователя, сгенерируй документ.
4. Команда генерации:
   ```bash
   cd report && PYTHONPATH=${CLAUDE_PLUGIN_ROOT} python -m doc_tpu generate -b content.md -r static.json -p report.docx
   ```

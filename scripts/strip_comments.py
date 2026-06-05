# -*- coding: utf-8 -*-
"""Удаление комментариев и docstrings из исходного кода проекта.

Скрипт безопасно вырезает из всех .py-файлов проекта:
  • строчные и хвостовые комментарии (``# ...``);
  • строки-документации (``\"\"\"...\"\"\"``) у модулей, классов и функций.

Безопасность («без вреда»):
  • файлы из .venv / build / dist / __pycache__ не трогаются;
  • результат каждого файла перед записью проверяется компилятором Python
    (``compile``). Если после очистки код перестаёт быть валидным —
    файл остаётся без изменений, а в консоль выводится предупреждение.

Запуск:  python scripts/strip_comments.py
"""

from __future__ import annotations

import io
import sys
import tokenize
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]      # корень проекта
# каталоги, которые трогать нельзя (чужой код, артефакты сборки, кэш)
EXCLUDE_DIRS = {".venv", "build", "dist", "__pycache__", ".git", ".build-cache"}
SELF = Path(__file__).resolve()                 # сам этот скрипт пропускаем


def iter_py_files():
    """Перебирает все .py-файлы проекта, кроме исключённых каталогов."""
    for path in ROOT.rglob("*.py"):
        # пропускаем файлы внутри исключённых каталогов
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.resolve() == SELF:              # себя не очищаем
            continue
        yield path


def strip_source(source: str) -> str:
    """Возвращает исходник без комментариев и docstrings.

    Алгоритм основан на модуле ``tokenize``: он разбирает код на токены
    и собирает его обратно, выбрасывая комментарии и строки-документации.
    Отступы и расположение кода при этом сохраняются.
    """
    output = []
    # читаем все токены сразу — пригодится заглядывать на следующий токен
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))

    # типы токенов, означающие «начало логической строки» (перед statement)
    line_starts = (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                   tokenize.DEDENT, tokenize.ENCODING)

    prev_type = tokenize.NEWLINE   # тип предыдущего токена
    last_lineno = -1
    last_col = 0

    for i, (tok_type, tok_str, (sline, scol), (eline, ecol), _line) in enumerate(tokens):
        # перешли на новую строку — сбрасываем отсчёт колонок
        if sline > last_lineno:
            last_col = 0
        # восстанавливаем горизонтальные отступы между токенами
        if scol > last_col:
            output.append(" " * (scol - last_col))

        drop = False
        if tok_type == tokenize.COMMENT:
            drop = True  # комментарий — всегда выбрасываем
        elif tok_type == tokenize.STRING:
            # docstring — это строка, которая образует ОТДЕЛЬНЫЙ оператор:
            # стоит в начале логической строки и сразу за ней идёт перевод.
            # Строки-ключи и значения словарей такому условию не отвечают.
            next_type = tokens[i + 1][0] if i + 1 < len(tokens) else None
            if prev_type in line_starts and next_type == tokenize.NEWLINE:
                drop = True

        if not drop:
            output.append(tok_str)

        prev_type = tok_type
        last_col = ecol
        last_lineno = eline

    return "".join(output)


def collapse_blank_lines(text: str) -> str:
    """Сжимает подряд идущие пустые строки (их остаётся максимум одна)."""
    result = []
    blank = 0
    for line in text.splitlines():
        if line.strip() == "":
            blank += 1
            if blank > 1:
                continue        # вторую и далее подряд пустую строку пропускаем
        else:
            blank = 0
        result.append(line.rstrip())  # заодно убираем хвостовые пробелы
    return "\n".join(result).strip("\n") + "\n"


def process_file(path: Path) -> bool:
    """Очищает один файл. Возвращает True, если файл был изменён."""
    original = path.read_text(encoding="utf-8")
    try:
        stripped = strip_source(original)
        stripped = collapse_blank_lines(stripped)
        # ПРОВЕРКА БЕЗОПАСНОСТИ: результат обязан быть валидным Python-кодом
        compile(stripped, str(path), "exec")
    except (tokenize.TokenError, SyntaxError, IndentationError) as exc:
        print(f"  ! пропущен (не удалось безопасно очистить): {path} — {exc}")
        return False

    if stripped == original:
        return False                # менять нечего
    path.write_text(stripped, encoding="utf-8")
    return True


def main() -> None:
    """Очищает все подходящие файлы проекта и печатает отчёт."""
    # на Windows консоль бывает не в UTF-8 — переключаем вывод, чтобы
    # русский текст не ломался
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    changed = 0
    total = 0
    for path in iter_py_files():
        total += 1
        rel = path.relative_to(ROOT)
        if process_file(path):
            changed += 1
            print(f"  очищено: {rel}")
    print(f"\nГотово. Обработано файлов: {total}, изменено: {changed}.")


if __name__ == "__main__":
    # подсказка: вернуть код можно через  git checkout -- .
    main()

# -*- coding: utf-8 -*-
"""Шрифты приложения.

Единая типографика. На macOS — SF Pro (системный), на Windows — Segoe UI.
Размеры и начертания собраны здесь, чтобы не дублировать их по коду.
"""

import platform
from pathlib import Path


_CUSTOM_DIR = Path(__file__).resolve().parents[1] / "ui" / "fonts"


def _font_files():
    """Возвращает локальные пользовательские шрифты."""
    if not _CUSTOM_DIR.exists():
        return []
    return sorted(
        p for p in _CUSTOM_DIR.iterdir()
        if p.suffix.lower() in {".ttf", ".otf"}
    )


def _family_from_file(path):
    """Получает предполагаемое имя семейства из файла."""
    return path.stem.replace("_", " ").replace("-", " ")


def _custom_family(alias):
    """Выбирает пользовательское семейство по алиасу."""
    files = _font_files()
    # точное совпадение имени файла с алиасом (ui.ttf, display.ttf, mono.ttf)
    for path in files:
        if path.stem.lower() == alias:
            return _family_from_file(path)
    # для текста/заголовка подойдёт и первый попавшийся пользовательский шрифт
    if files and alias in {"ui", "display"}:
        return _family_from_file(files[0])
    return None

_SYSTEM = platform.system()

# системные шрифты по умолчанию для каждой ОС
if _SYSTEM == "Darwin":
    _UI = "SF Pro Text"
    _DISPLAY = "SF Pro Display"
    _MONO = "SF Mono"
elif _SYSTEM == "Windows":
    _UI = "Inter"
    _DISPLAY = "Inter"
    _MONO = "Consolas"
else:
    _UI = "Inter"
    _DISPLAY = "Inter"
    _MONO = "DejaVu Sans Mono"

# если в проекте лежат свои шрифты — они в приоритете над системными
_UI = _custom_family("ui") or _UI
_DISPLAY = _custom_family("display") or _DISPLAY
_MONO = _custom_family("mono") or _MONO

FONTS = {
    "hero":      (_DISPLAY, 30, "bold"),
    "title":     (_DISPLAY, 18, "bold"),
    "heading":   (_DISPLAY, 14, "bold"),
    "subhead":   (_UI, 11, "bold"),
    "body":      (_UI, 11),
    "body_bold": (_UI, 11, "bold"),
    "small":     (_UI, 10),
    "caption":   (_UI, 9),
    "metric":    (_DISPLAY, 13, "bold"),
    "mono":      (_MONO, 10),
    "chart_title": (_DISPLAY, 13, "bold"),
    "chart_axis":  (_UI, 10),
    "chart_value": (_UI, 9, "bold"),
}


def font(role: str):
    """Возвращает кортеж шрифта по роли."""
    return FONTS.get(role, FONTS["body"])

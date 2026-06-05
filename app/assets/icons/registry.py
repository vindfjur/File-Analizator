# -*- coding: utf-8 -*-
"""Runtime loader for local PNG icons."""

from pathlib import Path
import tkinter as tk


ROOT = Path(__file__).resolve().parent

NAMES = {
    "open",
    "new",
    "check",
    "chart",
    "export",
    "add_row",
    "add_column",
    "delete",
    "clear",
    "rows",
    "columns",
    "format",
    "errors",
    "document",
}


class IconRegistry:
    """Caches PhotoImage objects so tkinter does not garbage-collect them."""

    def __init__(self):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        self._cache = {}

    def get(self, name, variant="metal"):
        """Возвращает иконку по имени и варианту."""
        if name not in NAMES:
            return None  # неизвестная иконка
        key = (name, variant)
        if key not in self._cache:
            # имя файла собирается как «<имя>_<вариант>.png»
            path = ROOT / f"{name}_{variant}.png"
            # ссылку на PhotoImage держим в кэше, иначе tkinter удалит картинку
            self._cache[key] = tk.PhotoImage(file=str(path))
        return self._cache[key]


# единый общий экземпляр реестра на всё приложение
registry = IconRegistry()

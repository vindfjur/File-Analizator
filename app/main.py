# -*- coding: utf-8 -*-
"""Анализатор файлов — настольное приложение на tkinter.

Возможности:
  • Загрузка файлов TXT, CSV, JSON и анализ их содержимого.
  • Создание нового проекта анализа с метаданными.
  • Просмотр данных в таблице, навигация по строкам и столбцам.
  • Редактирование ячеек, добавление/удаление строк и столбцов.
  • Фильтрация и сортировка данных.
  • Автоматическая проверка на ошибки с подсветкой.
  • Экспорт в CSV, JSON, Excel (xlsx), отчёт PDF, графики/диаграммы.
  • Светлая тема оформления в премиальном desktop-стиле.

Базовый функционал работает на стандартной библиотеке Python.
Расширения подключаются при наличии библиотек: openpyxl (Excel),
reportlab (PDF), Pillow (экспорт графиков).

Сам класс окна большой, поэтому его методы вынесены в mixin-модули
пакета ``app.window``. Здесь остаётся только «сборка» класса и базовый
жизненный цикл: создание, тема, открытие/создание проекта, статус.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .core.project import AnalysisProject
from .theme import colors, styles
from .ui.dialogs import NewProjectDialog
from .window.builders import UIBuilderMixin
from .window.table import TableMixin
from .window.exporting import ExportMixin
from .window.statistics import StatisticsMixin


class FileAnalyzerApp(UIBuilderMixin, TableMixin, ExportMixin,
                      StatisticsMixin, tk.Tk):
    """Главное окно приложения и координатор пользовательских сценариев.

    Класс собран из нескольких mixin-ов (порядок важен для MRO):
      • ``UIBuilderMixin``  — построение интерфейса;
      • ``TableMixin``      — работа с таблицей данных;
      • ``ExportMixin``     — сохранение и экспорт;
      • ``StatisticsMixin`` — сводки и окно статистики;
      • ``tk.Tk``           — само окно.
    """

    def __init__(self):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__()
        self.title("Анализатор файлов · Studio")
        self.geometry("1280x780")
        self.minsize(980, 620)  # ниже этого размера окно не сжимается

        # --- модель данных и общее состояние ---
        self.project = AnalysisProject()   # хранит столбцы, строки и метаданные
        self.is_dirty = False              # есть ли несохранённые изменения
        self.theme_name = "light"
        self.pal = colors.palette(self.theme_name)  # текущая палитра цветов
        self.bad_rows = set()              # индексы строк с ошибками
        self.bad_cells = set()             # пары (строка, столбец) с ошибками
        self.last_stats_column = None      # столбец из последнего окна статистики

        # --- переменные фильтра ---
        self.filter_text = tk.StringVar()
        self.filter_col = tk.StringVar(value="Все столбцы")

        # --- переменные строки состояния ---
        self.status_var = tk.StringVar(value="Готово")
        self.status_detail = tk.StringVar(value="—")

        # --- переменные верхней сводки (чип) ---
        self.stat_line = tk.StringVar(value="— • 0 строк • 0 столбцов • Ошибок нет")
        self.stat_rows = tk.StringVar(value="0")
        self.stat_cols = tk.StringVar(value="0")
        self.stat_format = tk.StringVar(value="—")
        self.stat_errors = tk.StringVar(value="Ошибок нет")

        # --- переменные карточки «Информация о файле» ---
        self.meta_name = tk.StringVar(value="Новый проект")
        self.meta_format = tk.StringVar(value="—")
        self.meta_encoding = tk.StringVar(value="—")
        self.meta_size = tk.StringVar(value="—")
        self.meta_rows = tk.StringVar(value="0")
        self.meta_cols = tk.StringVar(value="0")
        self.meta_status = tk.StringVar(value="Файл не загружен")

        # --- сборка интерфейса (методы из UIBuilderMixin) ---
        self.style = ttk.Style(self)
        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()
        self.apply_theme()
        self.refresh_table()
        self.update_meta_panel()

    def set_theme(self, _name="light"):
        """Принудительно применяет поддерживаемую светлую тему."""
        self.theme_name = "light"
        self.pal = colors.palette(self.theme_name)
        self.apply_theme()

    def apply_theme(self):
        """Применяет палитру и ttk-стили к текущему окну."""
        pal = colors.palette(self.theme_name)
        self.pal = pal
        styles.apply(self.style, pal)        # настраиваем все ttk-стили
        self.configure(bg=pal["bg"])
        styles.tree_tags(self.tree, pal)     # цвета строк таблицы (зебра/ошибка)
        self.refresh_table()

    def new_project(self):
        """Создаёт новый проект анализа через диалог метаданных."""
        dlg = NewProjectDialog(self)
        self.wait_window(dlg)        # ждём, пока пользователь закроет диалог
        if dlg.result:               # пользователь нажал «Создать»
            self.project.reset(**dlg.result)
            self._set_dirty(False)
            self.bad_rows = set()
            self.bad_cells = set()
            self.last_stats_column = None
            self.refresh_table()
            self.update_meta_panel()
            self.set_status(f"Создан проект: {self.project.meta['name']}")

    def open_file(self):
        """Открывает пользовательский файл и загружает его в проект."""
        path = filedialog.askopenfilename(
            title="Открыть файл",
            filetypes=[("Поддерживаемые", "*.txt *.csv *.json"),
                       ("Текст", "*.txt"), ("CSV", "*.csv"),
                       ("JSON", "*.json"), ("Все файлы", "*.*")])
        if not path:
            return  # диалог закрыт без выбора
        ext = os.path.splitext(path)[1].lower()  # выбираем загрузчик по расширению
        try:
            if ext == ".csv":
                self.project.load_csv(path)
            elif ext == ".json":
                self.project.load_json(path)
            else:
                self.project.load_txt(path)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки",
                                 f"Не удалось открыть файл:\n{e}")
            return
        # сбрасываем состояние и обновляем интерфейс под новый файл
        self.bad_rows = set()
        self.bad_cells = set()
        self.last_stats_column = None
        self._set_dirty(False)
        self.refresh_table()
        self.update_meta_panel()
        self.set_status(f"Загружено: {os.path.basename(path)} "
                        f"({len(self.project.rows)} строк)")

    def _set_dirty(self, value=True):
        """Запоминает, есть ли ручные изменения, которые можно сохранить."""
        self.is_dirty = bool(value)

    def show_about(self):
        """Показывает краткую информацию о приложении."""
        messagebox.showinfo(
            "О программе",
            "Анализатор файлов\n\n"
            "Детальный анализ содержимого и свойств файлов "
            "форматов TXT, CSV, JSON.\n\n"
            "• Просмотр, редактирование, фильтрация и сортировка данных\n"
            "• Проверка на ошибки с подсветкой\n"
            "• Экспорт в CSV / JSON / Excel / PDF / графики\n"
            "• Светлая премиальная тема\n\n"
            "Написано на Python + tkinter.")

    def set_status(self, text):
        """Обновляет текст нижней строки состояния."""
        self.status_var.set(text)


def main():
    """Запускает desktop-приложение."""
    app = FileAnalyzerApp()
    app.mainloop()


if __name__ == "__main__":
    main()

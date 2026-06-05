# -*- coding: utf-8 -*-
"""Сводки и статистика: верхний чип, карточка метаданных, окно статистики.

Mixin обновляет текстовые показатели (StringVar) и открывает окно
со статистикой. Сами графики рисует модуль ``ui.chart``.
"""

from tkinter import messagebox

from ..core.project import AnalysisProject
from ..theme import colors
from ..ui import chart


class StatisticsMixin:
    """Методы пересчёта сводок и работы со статистикой/графиками."""

    @staticmethod
    def _plural(n, one, few, many):
        """Возвращает русскую форму слова для числового значения."""
        # выбор формы: 1 строка / 2 строки / 5 строк
        n_abs = abs(n) % 100
        n1 = n_abs % 10
        if 10 < n_abs < 20:          # 11..19 — всегда форма «много»
            word = many
        elif n1 == 1:                # ...1 (кроме 11) — «одна»
            word = one
        elif 2 <= n1 <= 4:           # ...2..4 (кроме 12..14) — «несколько»
            word = few
        else:
            word = many
        return f"{n} {word}"

    def update_stats(self):
        """Обновляет верхнюю компактную сводку по файлу."""
        rows = len(self.project.rows)
        cols = len(self.project.columns)
        errors = len(self.bad_rows)
        self.stat_rows.set(self._plural(rows, "строка", "строки", "строк"))
        self.stat_cols.set(self._plural(cols, "столбец", "столбца", "столбцов"))
        self.stat_format.set(self.project.meta.get("file_format") or "—")
        self.stat_errors.set(
            "Ошибок нет" if errors == 0
            else self._plural(errors, "ошибка", "ошибки", "ошибок")
        )
        # собираем единую строку для чипа-сводки
        self.stat_line.set(
            f"{self.stat_format.get()} • {self.stat_rows.get()} • "
            f"{self.stat_cols.get()} • {self.stat_errors.get()}"
        )
        if hasattr(self, "stat_pill"):
            self.stat_pill.set_health(errors == 0)  # зелёная/жёлтая точка

    def update_meta_panel(self):
        """Обновляет карточку информации о файле и статусбар."""
        m = self.project.meta
        self.meta_name.set(m["name"] or "Новый проект")
        self.meta_format.set(m["file_format"] or "—")
        self.meta_encoding.set(m["encoding"] or "—")
        self.meta_size.set(m["file_size"] or "—")
        self.meta_rows.set(str(len(self.project.rows)))
        self.meta_cols.set(str(len(self.project.columns)))
        self.meta_status.set(
            "Файл успешно загружен" if m["source_file"]
            else "Ожидание файла"
        )
        # зелёный статус-блок виден только когда файл реально загружен
        if hasattr(self, "meta_status_block"):
            if m["source_file"]:
                if not self.meta_status_block.winfo_ismapped():
                    self.meta_status_block.pack(side="bottom", fill="x", pady=(16, 0))
            else:
                if self.meta_status_block.winfo_ismapped():
                    self.meta_status_block.pack_forget()
        # правый угол статусбара: кодировка · формат · размер
        detail = " · ".join(
            part for part in (m["encoding"], m["file_format"], m["file_size"])
            if part
        )
        self.status_detail.set(detail or "—")
        self.update_stats()

    def _model_for(self, col):
        """Создаёт модель диаграммы для выбранного столбца."""
        ci = self.project.columns.index(col)
        values = [r[ci] if ci < len(r) else "" for r in self.project.rows]
        return chart.build_model(col, values, AnalysisProject._is_number)

    def _default_chart_column(self):
        """Выбирает первый подходящий столбец для экспорта графика."""
        # ищем столбец, где хотя бы 2 числовых значения — он информативнее
        for ci, col in enumerate(self.project.columns):
            values = [r[ci] if ci < len(r) else "" for r in self.project.rows]
            numeric = [
                v for v in values
                if str(v).strip() and AnalysisProject._is_number(v)
            ]
            if len(numeric) >= 2:
                return col
        # ничего числового — берём первый столбец
        return self.project.columns[0] if self.project.columns else None

    def _chart_export_column(self):
        """Возвращает последний столбец статистики или резервный автоподбор."""
        if self.last_stats_column in self.project.columns:
            return self.last_stats_column
        return self._default_chart_column()

    def _remember_stats_column(self, column):
        """Запоминает столбец, открытый в окне статистики последним."""
        if column in self.project.columns:
            self.last_stats_column = column

    def show_statistics(self):
        """Открывает единое окно статистики без лишних диалогов."""
        if not self.project.columns:
            messagebox.showinfo("Нет данных", "Сначала загрузите данные.")
            return
        self.recalculate_errors()
        chart.StatisticsWindow(
            self,
            self.project,
            colors.palette(self.theme_name),
            self.bad_cells,
            initial_column=self.last_stats_column,
            # колбэк, чтобы запомнить выбранный пользователем столбец
            on_column_change=self._remember_stats_column,
        )

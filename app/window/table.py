# -*- coding: utf-8 -*-
"""Работа с таблицей: показ данных, фильтр, сортировка, правка, ошибки.

Mixin держит всё, что связано с виджетом ``self.tree`` и отображением
строк проекта. Сама модель данных живёт в ``AnalysisProject``.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog

from ..theme import fonts


class TableMixin:
    """Методы отрисовки и редактирования рабочей таблицы."""

    def _tree_yview(self, *args):
        """Прокручивает таблицу по вертикали и обновляет overlay ошибок."""
        self.tree.yview(*args)
        self._schedule_error_overlays()

    def _tree_xview(self, *args):
        """Прокручивает таблицу по горизонтали и обновляет overlay ошибок."""
        self.tree.xview(*args)
        self._schedule_error_overlays()

    def _schedule_error_overlays(self):
        """Планирует перерисовку overlay проблемных ячеек."""
        # after_idle — рисуем не сразу, а когда Tk закончит текущие события
        if hasattr(self, "tree"):
            self.after_idle(self.update_error_overlays)

    def clear_error_overlays(self):
        """Удаляет временные overlay-метки проблемных ячеек."""
        for overlay in getattr(self, "error_overlays", []):
            overlay.destroy()
        self.error_overlays = []

    def update_error_overlays(self):
        """Рисует мягкую подсветку только поверх видимых проблемных ячеек."""
        if not hasattr(self, "tree"):
            return
        self.clear_error_overlays()  # сначала убираем старые метки
        cols = list(self.project.columns)
        if not cols:
            return
        # перебираем строки, которые сейчас отрисованы в дереве
        for item in self.tree.get_children():
            try:
                row_idx = int(item)  # iid строки совпадает с индексом в данных
            except ValueError:
                continue
            for ci, col in enumerate(cols):
                if (row_idx, ci) not in self.bad_cells:
                    continue  # эта ячейка без ошибки — пропускаем
                bbox = self.tree.bbox(item, f"#{ci + 1}")  # координаты ячейки
                if not bbox:
                    continue  # ячейка вне видимой области
                x, y, w, h = bbox
                # текущее значение ячейки (для подписи поверх подсветки)
                raw = self.project.rows[row_idx][ci] if ci < len(self.project.rows[row_idx]) else ""
                value = str(raw).strip() or "пусто"
                # поверх ячейки кладём цветной Label с маркером «△»
                label = tk.Label(
                    self.tree,
                    text=f"{value}  △",
                    anchor="w",
                    bg=self.pal["error"],
                    fg=self.pal["danger"],
                    font=fonts.font("body"),
                    bd=0,
                    padx=8,
                )
                label.place(x=x + 1, y=y + 1, width=max(1, w - 2), height=max(1, h - 2))
                # двойной клик по метке открывает ту же ячейку на редактирование
                label.bind("<Double-1>", lambda _e, item=item, ci=ci: self.edit_cell(item, ci))
                self.error_overlays.append(label)

    def _update_filter_combo(self):
        """Синхронизирует список доступных столбцов для фильтра."""
        values = ["Все столбцы"] + list(self.project.columns)
        self.filter_combo["values"] = values
        # если выбранный ранее столбец исчез — возвращаемся к «Все столбцы»
        if self.filter_col.get() not in values:
            self.filter_col.set("Все столбцы")

    def _filtered_indices(self):
        """Возвращает индексы строк, подходящих под текущий фильтр."""
        text = self.filter_text.get().strip().lower()
        col = self.filter_col.get()
        if not text:
            return list(range(len(self.project.rows)))  # фильтра нет — все строки
        result = []
        if col == "Все столбцы" or col not in self.project.columns:
            # ищем подстроку в любой ячейке строки
            for i, row in enumerate(self.project.rows):
                if any(text in str(v).lower() for v in row):
                    result.append(i)
        else:
            # ищем только в выбранном столбце
            ci = self.project.columns.index(col)
            for i, row in enumerate(self.project.rows):
                if ci < len(row) and text in str(row[ci]).lower():
                    result.append(i)
        return result

    def refresh_table(self):
        """Полностью перестраивает таблицу с учётом фильтра и валидации."""
        self.recalculate_errors()  # обновляем множества проблемных строк/ячеек
        cols = self.project.columns
        self.tree["columns"] = cols
        # настраиваем заголовки: текст + клик для сортировки
        for ci, c in enumerate(cols):
            self.tree.heading(c, text=c,
                              command=lambda i=ci: self.sort_column(i))
            # ширина столбца зависит от длины его имени (в разумных пределах)
            self.tree.column(c, width=max(90, min(280, len(str(c)) * 12)),
                             anchor="w", stretch=True)

        # очищаем старые overlay и строки перед повторным заполнением
        self.clear_error_overlays()
        for item in self.tree.get_children():
            self.tree.delete(item)

        # вставляем только отфильтрованные строки, чередуя «зебру»
        for n, idx in enumerate(self._filtered_indices()):
            row = self.project.rows[idx]
            # дополняем недостающие ячейки пустыми значениями
            display = [row[i] if i < len(row) else "" for i in range(len(cols))]
            if n % 2:
                tag = "stripe"
            else:
                tag = "normal"
            # iid = индекс строки в данных, чтобы потом легко находить её
            self.tree.insert("", "end", iid=str(idx), values=display, tags=(tag,))

        self._update_filter_combo()
        shown = len(self.tree.get_children())
        total = len(self.project.rows)
        # если показаны не все строки — поясняем это в статусе
        suffix = f" (показано {shown} из {total})" if shown != total else ""
        self.update_stats()
        self.on_selection_change()
        self.set_status(f"Строк: {total}, столбцов: {len(cols)}{suffix}")
        self._schedule_error_overlays()

    def recalculate_errors(self):
        """Пересчитывает проблемные строки и ячейки без всплывающих окон."""
        if not self.project.columns or not self.project.rows:
            self.bad_rows = set()
            self.bad_cells = set()
            return
        # сами проверки выполняет модель проекта
        self.bad_rows, self.bad_cells, _messages = self.project.validate_detail()

    def sort_column(self, col_index):
        """Сортирует данные проекта по выбранному столбцу."""
        desc = self._sort_state.get(col_index, False)  # текущее направление
        self.project.sort_by(col_index, descending=desc)
        self._set_dirty(True)
        self._sort_state[col_index] = not desc  # следующий клик — наоборот
        self.refresh_table()
        arrow = "▼" if desc else "▲"
        self.set_status(f"Сортировка по «{self.project.columns[col_index]}» {arrow}")

    def clear_filter(self):
        """Сбрасывает текстовый и столбцовый фильтры."""
        self.filter_text.set("")
        self.filter_col.set("Все столбцы")
        self.refresh_table()

    def on_selection_change(self, _event=None):
        """Показывает или скрывает действие удаления при выборе строк."""
        if hasattr(self, "delete_btn"):
            if self.tree.selection():
                # есть выделение — показываем кнопку удаления, если она скрыта
                if not self.delete_btn.winfo_ismapped():
                    self.delete_btn.pack(side=tk.LEFT, padx=(8, 0))
            else:
                # выделения нет — убираем кнопку
                if self.delete_btn.winfo_ismapped():
                    self.delete_btn.pack_forget()

    def on_cell_edit(self, event):
        """Определяет ячейку под курсором и запускает редактирование."""
        if not self.project.columns:
            return
        item = self.tree.identify_row(event.y)      # строка под курсором
        column = self.tree.identify_column(event.x)  # столбец под курсором
        if not item or not column:
            return
        ci = int(column.replace("#", "")) - 1  # "#1" -> индекс 0
        if ci < 0 or ci >= len(self.project.columns):
            return
        self.edit_cell(item, ci)

    def edit_cell(self, item, ci):
        """Создаёт встроенное поле редактирования для ячейки таблицы."""
        x, y, w, h = self.tree.bbox(item, f"#{ci + 1}")  # геометрия ячейки
        if not w or not h:
            return
        self.clear_error_overlays()  # убираем подсветку, чтобы не мешала вводу
        value = self.tree.set(item, self.project.columns[ci])
        value = value.replace("  ⚠", "")  # убираем служебный маркер ошибки

        # поверх ячейки кладём временное поле ввода
        edit = tk.Entry(self.tree)
        edit.insert(0, value)
        edit.select_range(0, tk.END)
        edit.focus_set()
        edit.place(x=x, y=y, width=w, height=h)

        def commit(_=None):
            """Сохраняет введённое значение в модель данных."""
            new_val = edit.get()
            row_idx = int(item)
            row = self.project.rows[row_idx]
            while len(row) <= ci:  # добиваем строку до нужной длины
                row.append("")
            if row[ci] != new_val:  # отмечаем изменения только если значение поменялось
                row[ci] = new_val
                self._set_dirty(True)
            edit.destroy()
            self.refresh_table()
            self.update_meta_panel()
            self.set_status("Ячейка изменена")

        def cancel(_=None):
            """Закрывает редактор ячейки без сохранения."""
            edit.destroy()

        edit.bind("<Return>", commit)     # Enter — сохранить
        edit.bind("<FocusOut>", commit)   # уход фокуса — тоже сохранить
        edit.bind("<Escape>", cancel)     # Esc — отменить

    def add_row(self):
        """Добавляет пустую строку в текущую таблицу."""
        if not self.project.columns:
            messagebox.showinfo("Нет данных",
                                "Сначала откройте файл или создайте столбцы.")
            return
        self.project.add_row()
        self._set_dirty(True)
        self.refresh_table()
        self.update_meta_panel()
        # прокручиваем к новой строке и выделяем её
        children = self.tree.get_children()
        if children:
            self.tree.see(children[-1])
            self.tree.selection_set(children[-1])
        self.set_status("Добавлена строка")

    def delete_selected_rows(self):
        """Удаляет выбранные строки из проекта."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Удаление", "Выберите строки для удаления.")
            return
        indices = [int(i) for i in sel]  # iid -> индексы строк
        self.project.delete_rows(indices)
        self._set_dirty(True)
        self.refresh_table()
        self.update_meta_panel()
        self.set_status(f"Удалено строк: {len(indices)}")

    def add_column(self):
        """Добавляет столбец и пустые значения во все строки."""
        name = simpledialog.askstring("Новый столбец", "Имя столбца:",
                                      parent=self)
        if name:
            self.project.add_column(name.strip())
            self._set_dirty(True)
            self.refresh_table()
            self.update_meta_panel()
            self.set_status(f"Добавлен столбец «{name}»")

    def validate(self):
        """Возвращает совместимый результат проверки по строкам."""
        self.recalculate_errors()
        self.refresh_table()
        self.set_status("Данные проверены автоматически")

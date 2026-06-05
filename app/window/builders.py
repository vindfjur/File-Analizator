# -*- coding: utf-8 -*-
"""Сборка интерфейса: меню, тулбар, рабочая область и строка состояния.

Здесь только построение виджетов. Логика (что происходит по нажатию)
живёт в других mixin-ах, сюда она попадает через ``self.<метод>``.
"""

import tkinter as tk
from tkinter import ttk

from ..theme import fonts
from ..ui import components


class UIBuilderMixin:
    """Методы, которые один раз строят все элементы интерфейса окна."""

    def _build_menu(self):
        """Собирает нативное меню приложения."""
        menubar = tk.Menu(self)  # корневая полоса меню окна

        # --- меню «Файл»: работа с проектом и экспорт ---
        m_file = tk.Menu(menubar, tearoff=0)  # tearoff=0 — нельзя «оторвать» меню
        m_file.add_command(label="Новый проект…", command=self.new_project,
                           accelerator="Ctrl+N")
        m_file.add_command(label="Открыть файл…", command=self.open_file,
                           accelerator="Ctrl+O")
        m_file.add_command(label="Сохранить файл", command=self.save_file,
                           accelerator="Ctrl+S")
        m_file.add_separator()
        # вложенное подменю со всеми форматами экспорта
        m_export = tk.Menu(m_file, tearoff=0)
        m_export.add_command(label="CSV…", command=self.export_csv)
        m_export.add_command(label="JSON…", command=self.export_json)
        m_export.add_command(label="Excel (xlsx)…", command=self.export_excel)
        m_export.add_command(label="Отчёт PDF…", command=self.export_pdf)
        m_export.add_command(label="График (PNG)…", command=self.export_chart_image)
        m_file.add_cascade(label="Экспорт", menu=m_export)
        m_file.add_separator()
        m_file.add_command(label="Выход", command=self.quit)
        menubar.add_cascade(label="Файл", menu=m_file)

        # --- меню «Данные»: операции над таблицей ---
        m_data = tk.Menu(menubar, tearoff=0)
        m_data.add_command(label="Добавить строку", command=self.add_row)
        m_data.add_command(label="Удалить выбранные строки",
                           command=self.delete_selected_rows)
        m_data.add_command(label="Добавить столбец…", command=self.add_column)
        m_data.add_separator()
        m_data.add_command(label="Сбросить фильтр", command=self.clear_filter)
        m_data.add_command(label="Показать статистику…", command=self.show_statistics)
        menubar.add_cascade(label="Данные", menu=m_data)

        # --- меню «Справка» ---
        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=m_help)

        self.config(menu=menubar)  # подключаем готовое меню к окну
        # горячие клавиши дублируют пункты меню
        self.bind("<Control-n>", lambda e: self.new_project())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())

    def _build_toolbar(self):
        """Собирает верхний заголовок, сводку и панель действий."""
        # верхняя полоса с крупным заголовком и чипом-сводкой
        self.toolbar = ttk.Frame(self, style="App.TFrame", padding=(24, 24, 24, 8))
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        title_block = ttk.Frame(self.toolbar, style="App.TFrame")
        title_block.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(title_block, text="Анализатор файлов",
                  style="Hero.TLabel").pack(anchor="w")

        # чип со сводкой (формат, строки, столбцы, ошибки) справа вверху
        self.stat_pill = components.StatPill(self.toolbar, self.pal)
        self.stat_pill.pack(side=tk.RIGHT)
        self.stat_pill.set_info_var(self.stat_line)

        # вторая полоса — кнопки основных действий
        actions = ttk.Frame(self, style="App.TFrame", padding=(24, 8, 24, 16))
        actions.pack(side=tk.TOP, fill=tk.X)
        self.actions = actions  # запоминаем, чтобы привязать к ней меню экспорта
        components.ttk_button(actions, "open", "Открыть файл", self.open_file,
                              "Accent.TButton").pack(side=tk.LEFT, padx=(0, 8))
        components.ttk_button(actions, "new", "Новый проект", self.new_project)\
            .pack(side=tk.LEFT, padx=(0, 8))
        components.ttk_button(actions, "chart", "Статистика", self.show_statistics)\
            .pack(side=tk.LEFT, padx=(0, 8))
        components.ttk_button(actions, "export", "Экспорт", self.show_export_menu)\
            .pack(side=tk.LEFT, padx=(0, 8))

        # блок фильтра прижат к правому краю полосы действий
        filter_box = ttk.Frame(actions, style="App.TFrame")
        filter_box.pack(side=tk.RIGHT)
        ttk.Label(filter_box, text="Фильтр", style="Secondary.TLabel")\
            .pack(side=tk.LEFT, padx=(0, 8))
        # выпадающий список выбора столбца для фильтрации
        self.filter_combo = ttk.Combobox(filter_box, width=18,
                                          textvariable=self.filter_col,
                                          state="readonly")
        self.filter_combo.pack(side=tk.LEFT, padx=(0, 8))
        # поле ввода искомого текста
        entry = ttk.Entry(filter_box, textvariable=self.filter_text, width=30)
        entry.pack(side=tk.LEFT, padx=(0, 8))
        entry.bind("<KeyRelease>", lambda e: self.refresh_table())  # фильтр на лету
        # кнопка-крестик для сброса фильтра
        components.icon_button(filter_box, "clear", self.clear_filter)\
            .pack(side=tk.LEFT)

    def _build_body(self):
        """Собирает основную рабочую область с метаданными и таблицей."""
        body = ttk.Frame(self, style="App.TFrame", padding=(24, 0, 24, 16))
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # делитель: слева карточка с инфо о файле, справа таблица
        paned = ttk.PanedWindow(body, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- левая колонка: метаданные файла ---
        left_wrap = ttk.Frame(paned, style="App.TFrame", width=248)
        left_wrap.pack_propagate(False)  # фиксируем ширину колонки
        paned.add(left_wrap, weight=0)
        self.meta_card = components.GlassCard(left_wrap, self.pal, padding=14)
        self.meta_card.pack(fill=tk.BOTH, expand=True, padx=(0, 16))

        components.panel_label(self.meta_card.content, self.pal,
                               "Информация о файле", "subhead")\
            .pack(anchor="w")
        # строки метаданных: «название значение», привязаны к StringVar
        self.meta_rows_widgets = [
            components.MetaRow(self.meta_card.content, self.pal,
                               "Название", self.meta_name),
            components.MetaRow(self.meta_card.content, self.pal,
                               "Формат", self.meta_format),
            components.MetaRow(self.meta_card.content, self.pal,
                               "Кодировка", self.meta_encoding),
            components.MetaRow(self.meta_card.content, self.pal,
                               "Размер", self.meta_size),
            components.MetaRow(self.meta_card.content, self.pal,
                               "Количество строк", self.meta_rows),
            components.MetaRow(self.meta_card.content, self.pal,
                               "Количество столбцов", self.meta_cols),
        ]
        for row in self.meta_rows_widgets:
            row.pack(fill=tk.X, pady=(9, 0))
        # зелёный блок статуса внизу карточки (виден после загрузки файла)
        self.meta_status_block = components.StatusBlock(
            self.meta_card.content, self.pal, self.meta_status)
        self.meta_status_block.pack(side=tk.BOTTOM, fill=tk.X, pady=(14, 0))

        # --- правая колонка: рабочая таблица ---
        right_wrap = ttk.Frame(paned, style="App.TFrame")
        paned.add(right_wrap, weight=1)
        self.table_card = components.GlassCard(right_wrap, self.pal, padding=16)
        self.table_card.pack(fill=tk.BOTH, expand=True)

        # шапка таблицы: заголовок слева, кнопки операций справа
        table_top = tk.Frame(self.table_card.content, bg=self.pal["glass"], bd=0)
        table_top.pack(fill=tk.X, pady=(0, 12))
        tk.Label(table_top, text="Рабочая таблица", bg=self.pal["glass"],
                 fg=self.pal["fg"], font=fonts.font("heading"))\
            .pack(side=tk.LEFT)

        table_actions = tk.Frame(table_top, bg=self.pal["glass"], bd=0)
        table_actions.pack(side=tk.RIGHT)
        components.ttk_button(table_actions, "add_row", "Строка", self.add_row,
                              "Link.TButton").pack(side=tk.LEFT, padx=(0, 4))
        components.ttk_button(table_actions, "add_column", "Столбец",
                              self.add_column, "Link.TButton")\
            .pack(side=tk.LEFT, padx=(0, 4))
        # кнопка удаления создаётся, но показывается только при выделении строк
        self.delete_btn = ttk.Button(
            table_actions, text="Удалить выбранное",
            command=self.delete_selected_rows, style="DangerText.TButton")

        # --- сама таблица со скроллбарами ---
        tree_frame = tk.Frame(self.table_card.content, bg=self.pal["glass"], bd=0)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, show="headings", selectmode="extended")
        self.error_overlays = []  # наложенные метки проблемных ячеек
        # вертикальный и горизонтальный скроллбары идут через свои обёртки,
        # чтобы заодно перерисовывать подсветку ошибок при прокрутке
        ysb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self._tree_yview,
                            style="Thin.Vertical.TScrollbar")
        xsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                            command=self._tree_xview,
                            style="Thin.Horizontal.TScrollbar")
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        # раскладка через grid, чтобы скроллбары прилегали к таблице
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        xsb.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # обработчики событий таблицы
        self.tree.bind("<Double-1>", self.on_cell_edit)        # двойной клик — правка
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)
        # любое изменение видимой области требует пересчёта overlay-меток
        self.tree.bind("<Configure>", lambda _event: self._schedule_error_overlays())
        self.tree.bind("<MouseWheel>", lambda _event: self._schedule_error_overlays())
        self.tree.bind("<ButtonRelease-1>", lambda _event: self._schedule_error_overlays())
        self._sort_state = {}  # запоминаем направление сортировки по столбцам

    def _build_statusbar(self):
        """Собирает нижнюю строку состояния."""
        self.statusbar = ttk.Frame(self, style="App.TFrame", padding=(24, 0, 24, 16))
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        # слева — основное сообщение о действии
        self.status_lbl = ttk.Label(self.statusbar, textvariable=self.status_var,
                                     anchor="w", padding=(14, 8),
                                     style="Status.TLabel")
        self.status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # справа — краткие детали о файле (кодировка/формат/размер)
        self.status_detail_lbl = ttk.Label(
            self.statusbar,
            textvariable=self.status_detail,
            anchor="e",
            padding=(14, 8),
            style="Status.TLabel",
        )
        self.status_detail_lbl.pack(side=tk.RIGHT)

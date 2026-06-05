# -*- coding: utf-8 -*-
"""Модальные диалоги приложения."""

import tkinter as tk
from tkinter import ttk

from ..theme import colors, fonts
from . import components


class NewProjectDialog(tk.Toplevel):
    """Модальное окно создания нового проекта анализа."""
    def __init__(self, parent):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(parent)
        self.title("Новый проект анализа")
        self.resizable(False, False)         # размер окна фиксирован
        self.result = None                   # сюда попадут введённые данные
        self.transient(parent)               # окно поверх родителя
        self.grab_set()                      # модальность: блокируем остальное окно
        self.pal = colors.palette("light")
        self.configure(bg=self.pal["bg"])

        card = components.GlassCard(self, self.pal, padding=20)
        card.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
        frm = card.content

        tk.Label(frm, text="Новый проект анализа", bg=self.pal["glass"],
                 fg=self.pal["fg"], font=fonts.font("heading"))\
            .grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(frm, text="Метаданные сохраняются вместе с проектом",
                 bg=self.pal["glass"], fg=self.pal["secondary"],
                 font=fonts.font("small"))\
            .grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 16))

        tk.Label(frm, text="Название", bg=self.pal["glass"], fg=self.pal["fg"],
                 font=fonts.font("body"))\
            .grid(row=2, column=0, sticky="w", pady=6, padx=(0, 12))
        self.name = ttk.Entry(frm, width=34)
        self.name.insert(0, "Новый проект")
        self.name.grid(row=2, column=1, pady=6)

        tk.Label(frm, text="Автор", bg=self.pal["glass"], fg=self.pal["fg"],
                 font=fonts.font("body"))\
            .grid(row=3, column=0, sticky="w", pady=6, padx=(0, 12))
        self.author = ttk.Entry(frm, width=34)
        self.author.grid(row=3, column=1, pady=6)

        tk.Label(frm, text="Описание", bg=self.pal["glass"], fg=self.pal["fg"],
                 font=fonts.font("body"))\
            .grid(row=4, column=0, sticky="nw", pady=6, padx=(0, 12))
        self.desc = tk.Text(frm, width=26, height=4, relief="flat", bd=0,
                            padx=8, pady=8, bg=self.pal["entry"],
                            fg=self.pal["fg"], highlightthickness=1,
                            highlightbackground=self.pal["border"])
        self.desc.grid(row=4, column=1, pady=6)

        btns = tk.Frame(frm, bg=self.pal["glass"], bd=0)
        btns.grid(row=5, column=0, columnspan=2, pady=(18, 0), sticky="e")
        ttk.Button(btns, text="Создать", style="Accent.TButton",
                   command=self.ok).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Отмена", style="Ghost.TButton",
                   command=self.destroy).pack(side=tk.LEFT)

        self.name.focus_set()                          # курсор сразу в поле имени
        self.bind("<Return>", lambda e: self.ok())      # Enter — подтвердить
        self.bind("<Escape>", lambda e: self.destroy())  # Esc — закрыть

    def ok(self):
        """Сохраняет результат диалога и закрывает окно."""
        # собираем введённые значения; родитель прочитает их из self.result
        self.result = {
            "name": self.name.get().strip(),
            "author": self.author.get().strip(),
            "description": self.desc.get("1.0", tk.END).strip(),
        }
        self.destroy()


# -*- coding: utf-8 -*-
"""Переиспользуемые UI-компоненты премиального светлого интерфейса."""

import tkinter as tk
from tkinter import ttk

from ..assets.icons.registry import registry
from ..theme import fonts


# какой вариант иконки (по цвету) брать для конкретного стиля кнопки
STYLE_VARIANTS = {
    "Accent.TButton": "light",
    "Danger.TButton": "danger",
}


class GlassCard(tk.Frame):
    """Белая desktop-карточка с тонкой границей."""

    def __init__(self, master, pal, padding=16, **kwargs):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(master, bg=pal["bg"], bd=0, **kwargs)
        # внешняя рамка с тонкой границей
        self.body = tk.Frame(
            self,
            bg=pal["panel"],
            bd=0,
            highlightthickness=1,
            highlightbackground=pal["border"],
            highlightcolor=pal["accent_glow"],
        )
        self.body.pack(fill=tk.BOTH, expand=True)
        # внутренний контейнер с отступами — сюда кладут содержимое карточки
        self.content = tk.Frame(self.body, bg=pal["panel"], bd=0)
        self.content.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)


class StatPill(tk.Frame):
    """Нейтральный чип со сводкой по файлу.

    Раньше при наличии ошибок весь чип становился красным и читался
    как авария. Теперь фон всегда спокойный, а статус показывает
    только маленькая точка-индикатор (зелёная / янтарная).
    """

    def __init__(self, master, pal):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(
            master,
            bg=pal["chip_bg"],
            bd=0,
            padx=14,
            pady=7,
        )
        self.pal = pal
        self.health_icon = None
        self.health_label = None
        self.info_label = None
        self.dot = None

    def set_info_var(self, text_var):
        """Привязывает текстовую переменную к сводке."""
        self.dot = tk.Label(
            self,
            text="●",
            bg=self.pal["chip_bg"],
            fg=self.pal["success"],
            font=fonts.font("caption"),
        )
        self.dot.pack(side=tk.LEFT, padx=(0, 8))
        self.info_label = tk.Label(
            self,
            textvariable=text_var,
            bg=self.pal["chip_bg"],
            fg=self.pal["chip_fg"],
            font=fonts.font("body_bold"),
        )
        self.info_label.pack(side=tk.LEFT)

    def add_health_item(self, text_var):
        """Добавляет индикатор состояния к сводке."""
        item = tk.Frame(self, bg=self.pal["chip_bg"], bd=0)
        item.pack(side=tk.LEFT, padx=(10, 0))
        self.health_icon = tk.Label(item, bg=self.pal["chip_bg"], bd=0)
        self.health_icon.pack(side=tk.LEFT)
        self.health_label = tk.Label(
            item,
            textvariable=text_var,
            bg=self.pal["chip_bg"],
            fg=self.pal["success"],
            font=fonts.font("body_bold"),
        )
        self.health_label.pack(side=tk.LEFT, padx=(7, 0))
        self.set_health(True)

    def set_health(self, ok):
        """Обновляет визуальное состояние индикатора качества."""
        # точка-индикатор: зелёная при «всё хорошо», янтарная при ошибках
        if self.dot:
            self.dot.configure(
                fg=self.pal["success"] if ok else self.pal["warning"])
        if self.info_label:
            self.info_label.configure(fg=self.pal["chip_fg"])
        if not self.health_icon or not self.health_label:
            return  # дополнительного индикатора с иконкой нет
        icon = registry.get("check" if ok else "errors",
                            "success" if ok else "danger")
        self.health_icon.configure(image=icon)
        self.health_label.configure(
            fg=self.pal["success"] if ok else self.pal["warning"])


class MetaRow(tk.Frame):
    """Компактная строка метаданных без визуального шума."""

    def __init__(self, master, pal, title, value_var):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(master, bg=pal["panel"], bd=0)
        tk.Label(self, text=title, bg=pal["panel"], fg=pal["secondary"],
                 font=fonts.font("small")).pack(side=tk.LEFT)
        tk.Label(self, textvariable=value_var, bg=pal["panel"], fg=pal["fg"],
                 font=fonts.font("body_bold"), anchor="e", justify=tk.RIGHT,
                 wraplength=150).pack(side=tk.RIGHT)


class StatusBlock(tk.Frame):
    """Нижний статус в карточке информации о файле."""

    def __init__(self, master, pal, text_var):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(
            master,
            bg=pal["success_soft"],
            bd=0,
            highlightthickness=1,
            highlightbackground=pal["success"],
        )
        img = registry.get("check", "success")
        if img:
            tk.Label(self, image=img, bg=pal["success_soft"], bd=0)\
                .pack(side=tk.LEFT, padx=(10, 6), pady=9)
        tk.Label(self, textvariable=text_var, bg=pal["success_soft"],
                 fg=pal["success"], font=fonts.font("small"), anchor="w")\
            .pack(side=tk.LEFT, fill=tk.X, expand=True, pady=9, padx=(0, 10))


def panel_label(master, pal, text, role="body", color="fg"):
    """Label для tk-панелей, где ttk background хуже наследуется."""
    return tk.Label(master, text=text, bg=pal["panel"], fg=pal[color],
                    font=fonts.font(role))


def ttk_button(master, icon, label, command, style="Ghost.TButton"):
    """Создаёт ttk-кнопку с локальной PNG-иконкой."""
    variant = STYLE_VARIANTS.get(style, "metal")  # цвет иконки под стиль кнопки
    img = registry.get(icon, variant)
    # compound=LEFT — иконка слева от текста
    return ttk.Button(master, image=img, text=label, compound=tk.LEFT,
                      command=command, style=style)


def icon_button(master, icon, command, style="Ghost.TButton"):
    """Создаёт компактную иконку-кнопку."""
    variant = STYLE_VARIANTS.get(style, "metal")
    img = registry.get(icon, variant)
    return ttk.Button(master, image=img, command=command, style=style)

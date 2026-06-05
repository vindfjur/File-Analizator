# -*- coding: utf-8 -*-
"""Настройка дизайна ttk-виджетов.

Вся «раскраска» интерфейса живёт здесь: цвета берутся из ``colors``,
шрифты — из ``fonts``. В остальном коде нет прямых обращений к стилям.
"""

from tkinter import ttk

from . import fonts


def apply(style: "ttk.Style", pal: dict) -> None:
    """Конфигурирует глобальные ttk-стили под выбранную палитру."""
    style.theme_use("clam")  # «clam» лучше всего поддаётся перекраске

    base = fonts.font("body")
    # стиль "." — базовый, от него наследуются остальные виджеты
    style.configure(".", background=pal["bg"], foreground=pal["fg"],
                    fieldbackground=pal["entry"], bordercolor=pal["border"],
                    font=base)

    # --- контейнеры и подписи ---
    style.configure("TFrame", background=pal["bg"])
    style.configure("App.TFrame", background=pal["bg"])
    style.configure("Panel.TFrame", background=pal["panel"])
    style.configure("Glass.TFrame", background=pal["glass"])
    style.configure("Soft.TFrame", background=pal["panel_alt"])
    style.configure("TLabel", background=pal["bg"], foreground=pal["fg"],
                    font=base)
    style.configure("Hero.TLabel", background=pal["bg"],
                    foreground=pal["fg"], font=fonts.font("hero"))
    style.configure("Panel.TLabel", background=pal["panel"],
                    foreground=pal["fg"], font=base)
    style.configure("PanelSecondary.TLabel", background=pal["panel"],
                    foreground=pal["secondary"], font=fonts.font("small"))
    style.configure("Secondary.TLabel", background=pal["bg"],
                    foreground=pal["secondary"], font=fonts.font("small"))
    style.configure("Heading.TLabel", background=pal["bg"],
                    foreground=pal["fg"], font=fonts.font("heading"))
    style.configure("Metric.TLabel", background=pal["panel"],
                    foreground=pal["fg"], font=fonts.font("metric"))
    style.configure("MetricName.TLabel", background=pal["panel"],
                    foreground=pal["muted"], font=fonts.font("caption"))

    # --- кнопки (configure задаёт обычный вид, map — вид при наведении/нажатии) ---
    style.configure("TButton", background=pal["panel"], foreground=pal["fg"],
                    borderwidth=1, focuscolor=pal["accent"], padding=(16, 10),
                    font=fonts.font("body"))
    style.map("TButton",
              background=[("active", pal["accent"]), ("pressed", pal["accent"])],
              foreground=[("active", pal["accent_fg"]),
                          ("pressed", pal["accent_fg"])],
              bordercolor=[("active", pal["accent"])])

    style.configure("Accent.TButton", background=pal["accent"],
                    foreground=pal["accent_fg"], borderwidth=0,
                    padding=(16, 10), font=fonts.font("body_bold"))
    style.map("Accent.TButton",
              background=[("active", pal["accent2"]),
                          ("pressed", pal["accent2"])],
              foreground=[("active", pal["accent_fg"])])

    style.configure("Ghost.TButton", background=pal["panel_alt"],
                    foreground=pal["fg"], borderwidth=1,
                    bordercolor=pal["border"], padding=(16, 10),
                    font=fonts.font("body"))
    style.map("Ghost.TButton",
              background=[("active", pal["accent_soft"]),
                          ("pressed", pal["accent_soft"])],
              foreground=[("active", pal["accent"])],
              bordercolor=[("active", pal["accent_glow"])])

    style.configure("Text.TButton", background=pal["panel"],
                    foreground=pal["fg"], borderwidth=0,
                    padding=(8, 6), font=fonts.font("body_bold"))
    style.map("Text.TButton",
              background=[("active", pal["panel"])],
              foreground=[("active", pal["accent"])])

    style.configure("Link.TButton", background=pal["panel"],
                    foreground=pal["accent"], borderwidth=0,
                    padding=(8, 6), font=fonts.font("body_bold"))
    style.map("Link.TButton",
              background=[("active", pal["accent_soft"]),
                          ("pressed", pal["accent_soft"])],
              foreground=[("active", pal["accent"]),
                          ("pressed", pal["accent"])])

    style.configure("DangerText.TButton", background=pal["panel"],
                    foreground=pal["danger"], borderwidth=0,
                    padding=(8, 6), font=fonts.font("body_bold"))
    style.map("DangerText.TButton",
              background=[("active", pal["danger_soft"])],
              foreground=[("active", pal["danger"])])

    style.configure("Danger.TButton", background=pal["danger_soft"],
                    foreground=pal["danger"], borderwidth=1,
                    bordercolor=pal["danger_soft"], padding=(16, 10),
                    font=fonts.font("body"))
    style.map("Danger.TButton",
              background=[("active", pal["danger"]),
                          ("pressed", pal["danger"])],
              foreground=[("active", pal["accent_fg"]),
                          ("disabled", pal["disabled"])],
              bordercolor=[("disabled", pal["border_soft"])])

    # --- поля ввода и выпадающие списки ---
    style.configure("TEntry", fieldbackground=pal["entry"],
                    foreground=pal["fg"], insertcolor=pal["fg"],
                    borderwidth=1, bordercolor=pal["border"], padding=(10, 10))
    style.configure("TCombobox", fieldbackground=pal["entry"],
                    background=pal["panel"], foreground=pal["fg"],
                    arrowcolor=pal["secondary"], bordercolor=pal["border"],
                    padding=(10, 10))
    style.map("TCombobox",
              fieldbackground=[("readonly", pal["entry"])],
              foreground=[("readonly", pal["fg"])])

    style.configure("TSeparator", background=pal["border_soft"])

    # --- тонкие скроллбары: переопределяем раскладку (только «бегунок») ---
    style.layout("Thin.Vertical.TScrollbar", [
        ("Vertical.Scrollbar.trough", {
            "sticky": "ns",
            "children": [("Vertical.Scrollbar.thumb",
                          {"expand": "1", "sticky": "nswe"})],
        }),
    ])
    style.layout("Thin.Horizontal.TScrollbar", [
        ("Horizontal.Scrollbar.trough", {
            "sticky": "we",
            "children": [("Horizontal.Scrollbar.thumb",
                          {"expand": "1", "sticky": "nswe"})],
        }),
    ])
    for orient in ("Thin.Vertical.TScrollbar", "Thin.Horizontal.TScrollbar"):
        style.configure(orient, background=pal["scroll_thumb"],
                        troughcolor=pal["scroll_trough"],
                        bordercolor=pal["scroll_trough"],
                        lightcolor=pal["scroll_thumb"],
                        darkcolor=pal["scroll_thumb"],
                        arrowcolor=pal["scroll_trough"], width=6)
        style.map(orient,
                  background=[("active", pal["scroll_thumb_active"]),
                              ("pressed", pal["scroll_thumb_active"])])

    style.configure("Status.TLabel", background=pal["bg"],
                    foreground=pal["muted"], font=fonts.font("small"))

    # --- таблица (Treeview): тело и заголовки столбцов ---
    style.configure("Treeview", background=pal["tree_bg"],
                    foreground=pal["tree_fg"], fieldbackground=pal["tree_bg"],
                    rowheight=30, borderwidth=0, font=fonts.font("body"))
    style.map("Treeview", background=[("selected", pal["tree_sel"])],
              foreground=[("selected", pal["fg"])])
    style.configure("Treeview.Heading", background=pal["heading"],
                    foreground=pal["heading_fg"], relief="flat",
                    borderwidth=0, padding=(8, 10),
                    font=fonts.font("caption"))
    style.map("Treeview.Heading",
              background=[("active", pal["heading"]),
                          ("pressed", pal["heading"])],
              foreground=[("active", pal["secondary"])],
              relief=[("active", "flat"), ("pressed", "flat")])


def tree_tags(tree: "ttk.Treeview", pal: dict) -> None:
    """Настраивает теги строк таблицы (зебра / ошибка)."""
    tree.tag_configure("error", background=pal["error"], foreground=pal["danger"])
    tree.tag_configure("stripe", background=pal["stripe"], foreground=pal["tree_fg"])
    tree.tag_configure("normal", background=pal["tree_bg"], foreground=pal["tree_fg"])

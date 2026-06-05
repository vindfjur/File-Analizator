# -*- coding: utf-8 -*-
"""Цветовые палитры приложения.

Здесь собраны ВСЕ цвета. Меняй внешний вид только отсюда —
ни в одном другом файле не должно быть «зашитых» hex-кодов.
Палитра сфокусирована на светлой, нейтральной теме.
"""

LIGHT = {
    "bg":         "#F7F8FA",
    "bg_top":     "#FFFFFF",
    "bg_bottom":  "#F7F8FA",
    "panel":      "#FFFFFF",
    "panel_alt":  "#FFFFFF",
    "glass":      "#FFFFFF",
    "glass_soft": "#F8F9FB",
    "entry":      "#FFFFFF",
    "fg":         "#111827",
    "secondary":  "#6B7280",
    "muted":      "#9CA3AF",
    "disabled":   "#C7CDD6",
    "accent":     "#111827",
    "accent2":    "#374151",
    "accent_soft": "#F3F4F6",
    "accent_glow": "#E5E7EB",
    "accent_fg":  "#FFFFFF",
    "tree_bg":    "#FFFFFF",
    "tree_fg":    "#1F2937",
    "tree_sel":   "#F1F5F9",
    "heading":    "#FAFBFC",
    "heading_fg": "#9CA3AF",
    "heading_border": "#EEF0F3",
    "stripe":     "#FCFCFD",
    "hover":      "#FAFBFC",
    "error":      "#FEF6F6",
    "border":     "#E5E7EB",
    "border_soft": "#F1F3F5",
    "shadow":     "#E5E7EB",
    "grid":       "#F1F3F5",
    "success":    "#16A34A",
    "warning":    "#D97706",
    "warning_soft": "#FFFBEB",
    "danger":     "#DC2626",
    "danger_soft": "#FEF2F2",
    "danger_mute": "#E2999B",
    "success_soft": "#ECFDF3",
    "chip_bg":    "#F3F4F6",
    "chip_fg":    "#4B5563",
    "scroll_thumb": "#D5D9E0",
    "scroll_thumb_active": "#B9BFC9",
    "scroll_trough": "#FFFFFF",
}

THEMES = {"light": LIGHT}


def palette(name: str) -> dict:
    """Возвращает палитру по имени темы (фолбэк — светлая)."""
    return THEMES.get(name, LIGHT)

# -*- coding: utf-8 -*-
"""Generate monochrome Lucide-style PNG icons for tkinter."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
SIZE = 64    # рисуем крупно, потом уменьшаем — края выходят гладкими
OUT = 24     # итоговый размер иконки в пикселях
STROKE = 4   # толщина линий

# цветовые варианты одной и той же иконки (по контексту использования)
COLORS = {
    "metal": "#2F363D",
    "light": "#FFFFFF",
    "muted": "#7F8A96",
    "danger": "#D83A3A",
    "success": "#2F8F5B",
}


def canvas(color):
    """Создаёт прозрачное изображение для генерации иконки."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img), color


def save(name, variant, img):
    """Сохраняет сгенерированную иконку."""
    path = ROOT / f"{name}_{variant}.png"
    img = img.resize((OUT, OUT), Image.Resampling.LANCZOS)  # уменьшаем со сглаживанием
    img.save(path)


def line(draw, points, color, width=STROKE):
    """Рисует линию в стиле icon pack."""
    draw.line(points, fill=color, width=width, joint="curve")


def rounded(draw, box, color, radius=8, width=STROKE):
    """Рисует скруглённый контур."""
    draw.rounded_rectangle(box, radius=radius, outline=color, width=width)


def icon_document(draw, color):
    """Рисует иконку документа."""
    rounded(draw, (18, 8, 46, 56), color, radius=5)
    line(draw, [(38, 8), (38, 20), (46, 20)], color)
    line(draw, [(25, 33), (39, 33)], color)
    line(draw, [(25, 42), (35, 42)], color)


def icon_folder(draw, color):
    """Рисует иконку папки."""
    line(draw, [(10, 24), (10, 50), (54, 50), (54, 22), (34, 22),
                (29, 16), (10, 16), (10, 24)], color)


def icon_plus(draw, color):
    """Рисует иконку плюса."""
    line(draw, [(32, 15), (32, 49)], color)
    line(draw, [(15, 32), (49, 32)], color)


def icon_check(draw, color):
    """Рисует иконку галочки."""
    line(draw, [(15, 34), (27, 46), (50, 19)], color)


def icon_chart(draw, color):
    """Рисует иконку диаграммы."""
    draw.arc((13, 13, 51, 51), start=25, end=335, fill=color, width=STROKE)
    line(draw, [(32, 32), (32, 13)], color)
    line(draw, [(32, 32), (49, 42)], color)


def icon_export(draw, color):
    """Рисует иконку экспорта."""
    rounded(draw, (14, 28, 50, 54), color, radius=5)
    line(draw, [(32, 10), (32, 38)], color)
    line(draw, [(22, 20), (32, 10), (42, 20)], color)


def icon_table(draw, color):
    """Рисует иконку таблицы."""
    rounded(draw, (12, 12, 52, 52), color, radius=6)
    line(draw, [(12, 26), (52, 26)], color)
    line(draw, [(12, 39), (52, 39)], color)
    line(draw, [(26, 12), (26, 52)], color)
    line(draw, [(39, 12), (39, 52)], color)


def icon_trash(draw, color):
    """Рисует иконку удаления."""
    line(draw, [(20, 21), (44, 21)], color)
    line(draw, [(27, 14), (37, 14)], color)
    rounded(draw, (23, 21, 41, 53), color, radius=4)
    line(draw, [(29, 28), (29, 46)], color, width=3)
    line(draw, [(35, 28), (35, 46)], color, width=3)


def icon_x(draw, color):
    """Рисует иконку сброса."""
    line(draw, [(20, 20), (44, 44)], color)
    line(draw, [(44, 20), (20, 44)], color)


def icon_rows(draw, color):
    """Рисует иконку строк."""
    for y in (18, 32, 46):
        line(draw, [(24, y), (51, y)], color)
        draw.rounded_rectangle((13, y - 3, 19, y + 3), radius=2, fill=color)


def icon_columns(draw, color):
    """Рисует иконку столбцов."""
    for x in (16, 31, 46):
        rounded(draw, (x - 5, 17, x + 5, 47), color, radius=3)


def icon_warning(draw, color):
    """Рисует иконку предупреждения."""
    line(draw, [(32, 12), (54, 51), (10, 51), (32, 12)], color)
    line(draw, [(32, 25), (32, 38)], color, width=3)
    draw.ellipse((29, 43, 35, 49), fill=color)


def render():
    """Генерирует все варианты локальных PNG-иконок."""
    # сопоставление: имя иконки -> функция, которая её рисует
    icons = {
        "document": icon_document,
        "open": icon_folder,
        "new": icon_plus,
        "check": icon_check,
        "chart": icon_chart,
        "export": icon_export,
        "add_row": icon_rows,
        "add_column": icon_table,
        "delete": icon_trash,
        "clear": icon_x,
        "rows": icon_rows,
        "columns": icon_columns,
        "format": icon_document,
        "errors": icon_warning,
    }
    # для каждого цвета рисуем полный набор иконок
    for variant, color in COLORS.items():
        for name, draw_icon in icons.items():
            img, draw, c = canvas(color)
            draw_icon(draw, c)  # вызываем нужную рисующую функцию
            save(name, variant, img)


if __name__ == "__main__":
    render()

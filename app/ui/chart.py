# -*- coding: utf-8 -*-
"""Современные графики без matplotlib.

Геометрия диаграммы вычисляется один раз (``build_layout``), а затем
рисуется двумя бэкендами с общим кодом:
  • ``ChartCanvas`` — нативный tk.Canvas с плавной анимацией (для окна);
  • ``render_image`` — Pillow-рендер высокого разрешения (для экспорта).

Так на экране и в файле получается одинаковый премиальный вид.
"""

import os
import tkinter as tk

from ..theme import fonts

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _hex_to_rgb(h):
    """Преобразует HEX-цвет в RGB-кортеж."""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    """Преобразует RGB-кортеж в HEX-цвет."""
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(c))) for c in rgb))


def _lerp_color(c1, c2, t):
    """Смешивает два цвета по коэффициенту."""
    a, b = _hex_to_rgb(c1), _hex_to_rgb(c2)
    return _rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def _nice_ticks(max_value, count=4):
    """Возвращает «красивые» отметки оси от 0 до значения ≥ max_value."""
    if max_value <= 0:
        return [0, 1], 1
    raw = max_value / count          # грубый шаг между отметками
    # порядок величины шага (10, 100, ...), чтобы подобрать круглый шаг
    mag = 10 ** (len(str(int(raw))) - 1) if raw >= 1 else 1
    # берём первый «красивый» множитель, при котором ось накрывает max_value
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step * count >= max_value:
            break
    top = step * count                       # верхняя граница оси
    ticks = [i * step for i in range(count + 1)]  # сами отметки
    return ticks, top


def build_model(column, values, is_number):
    """Histogram для числового столбца, частоты — для категориального."""
    # помечаем непустые числовые значения
    flags = [is_number(v) and str(v).strip() != "" for v in values]
    # столбец числовой, если больше 60% значений — числа
    numeric = bool(values) and sum(flags) / max(1, len(values)) > 0.6

    if numeric:
        # для чисел строим гистограмму распределения
        nums = [float(str(v).replace(",", ".")) for v, ok in zip(values, flags) if ok]
        series = _histogram(nums)
        return {
            "kind": "hist",
            "title": f"Распределение значений · {column}",
            "x_label": column, "y_label": "Частота",
            "series": series, "orientation": "vertical",
        }

    # для текста считаем частоту каждого значения
    counts = {}
    for v in values:
        key = str(v) if str(v).strip() else "(пусто)"
        counts[key] = counts.get(key, 0) + 1
    # оставляем 15 самых частых значений
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:15]
    return {
        "kind": "bar",
        "title": f"Частота значений · {column} (топ-15)",
        "x_label": "Количество", "y_label": column,
        "series": top, "orientation": "horizontal",
    }


def _histogram(nums):
    """Группирует числовые значения в интервалы гистограммы."""
    lo, hi = min(nums), max(nums)
    if lo == hi:
        return [(f"{lo:g}", len(nums))]  # все значения одинаковы — один столбец
    # число интервалов: от 5 до 20, по количеству уникальных значений
    bins = min(20, max(5, len(set(nums))))
    width = (hi - lo) / bins              # ширина одного интервала
    counts = [0] * bins
    for n in nums:
        # номер интервала для значения (последний край включаем в крайний bin)
        idx = min(bins - 1, int((n - lo) / width))
        counts[idx] += 1
    series = []
    for i, c in enumerate(counts):
        left = lo + i * width             # левая граница интервала — подпись
        series.append((f"{left:g}", c))
    return series


def _truncate(s, n):
    """Обрезает длинную строку до заданной длины."""
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + "…"


def build_layout(model, width, height, pal):
    """Считает прямоугольники столбцов, сетку и подписи."""
    series = model["series"] or [("—", 0)]
    horizontal = model["orientation"] == "horizontal"
    # отступы вокруг области графика (слева больше — под подписи категорий)
    pad_l = 150 if horizontal else 56
    pad_r = 28
    pad_t = 58
    pad_b = 64 if not horizontal else 44
    plot = (pad_l, pad_t, width - pad_r, height - pad_b)  # прямоугольник графика
    px0, py0, px1, py1 = plot

    max_v = max(v for _, v in series) or 1  # максимум данных задаёт масштаб
    ticks, top = _nice_ticks(max_v)         # «красивые» отметки и верх оси

    bars, grid, labels = [], [], []
    n = len(series)

    if horizontal:
        # горизонтальные столбцы: распределяем по вертикали
        gap = 8
        slot = (py1 - py0) / n          # высота слота под один столбец
        bar_h = max(8, slot - gap)
        for i, (label, value) in enumerate(series):
            cy = py0 + slot * i + gap / 2
            x_end = px0 + (px1 - px0) * (value / top)  # длина столбца по значению
            # цвет — плавный переход от accent к accent2 по индексу
            fill = _lerp_color(pal["accent"], pal["accent2"], i / max(1, n - 1))
            bars.append({"x0": px0, "y0": cy, "x1": x_end, "y1": cy + bar_h,
                         "grow": "right", "fill": fill,
                         "value": value, "value_text": str(value)})
            # подпись категории слева от столбца
            labels.append((_truncate(label, 22), px0 - 12, cy + bar_h / 2,
                           "e"))
        for t in ticks:  # вертикальные линии сетки + подписи оси X
            gx = px0 + (px1 - px0) * (t / top)
            grid.append((gx, py0, gx, py1, f"{t:g}"))
    else:
        # вертикальные столбцы: распределяем по горизонтали
        gap = max(6, (px1 - px0) / n * 0.28)
        slot = (px1 - px0) / n          # ширина слота под один столбец
        bar_w = max(6, slot - gap)
        for i, (label, value) in enumerate(series):
            cx = px0 + slot * i + gap / 2
            y_top = py1 - (py1 - py0) * (value / top)  # верх столбца по значению
            fill = _lerp_color(pal["accent"], pal["accent2"], i / max(1, n - 1))
            bars.append({"x0": cx, "y0": y_top, "x1": cx + bar_w, "y1": py1,
                         "grow": "up", "fill": fill,
                         "value": value, "value_text": str(value)})
            if n <= 12:  # подписи снизу показываем, только если столбцов немного
                labels.append((_truncate(label, 8), cx + bar_w / 2, py1 + 10,
                               "n"))
        for t in ticks:  # горизонтальные линии сетки + подписи оси Y
            gy = py1 - (py1 - py0) * (t / top)
            grid.append((px0, gy, px1, gy, f"{t:g}"))

    return {
        "width": width, "height": height, "plot": plot,
        "bars": bars, "grid": grid, "labels": labels,
        "title": model["title"], "x_label": model["x_label"],
        "y_label": model["y_label"], "horizontal": horizontal,
    }


class ChartCanvas(tk.Canvas):
    """Рисует диаграмму на Canvas и плавно «выращивает» столбцы."""

    CORNER = 7

    def __init__(self, master, model, pal, **kw):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(master, highlightthickness=0, bd=0,
                         bg=pal["panel"], **kw)
        self.model = model
        self.pal = pal
        self._progress = 0.0
        self._anim_job = None
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, _event=None):
        """Перерисовывает canvas после изменения размера."""
        self.redraw(animate=False)

    def show(self):
        """Первая отрисовка с анимацией появления."""
        self._progress = 0.0
        self._animate()

    def _animate(self):
        """Выполняет следующий шаг анимации."""
        self._progress = min(1.0, self._progress + 0.08)  # +8% прогресса за кадр
        self.redraw(progress=self._ease(self._progress))
        if self._progress < 1.0:
            self._anim_job = self.after(16, self._animate)  # ~60 кадров в секунду

    @staticmethod
    def _ease(t):
        """Считает ease-out коэффициент анимации."""
        return 1 - (1 - t) ** 3   # ease-out cubic

    def redraw(self, progress=1.0, animate=True):
        """Перерисовывает содержимое canvas."""
        self.delete("all")  # стираем прошлый кадр
        w = self.winfo_width() or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        if w < 50 or h < 50:
            return  # окно ещё слишком маленькое — рисовать нечего
        lay = build_layout(self.model, w, h, self.pal)  # геометрия графика
        pal = self.pal

        # заголовок графика
        self.create_text(lay["plot"][0], 24, text=lay["title"], anchor="w",
                         fill=pal["fg"], font=fonts.font("chart_title"))

        # линии сетки и подписи осей
        for gx0, gy0, gx1, gy1, tlabel in lay["grid"]:
            self.create_line(gx0, gy0, gx1, gy1, fill=pal["grid"])
            if lay["horizontal"]:
                self.create_text(gx0, gy1 + 14, text=tlabel, fill=pal["secondary"],
                                 font=fonts.font("chart_axis"))
            else:
                self.create_text(lay["plot"][0] - 10, gy0, text=tlabel,
                                 anchor="e", fill=pal["secondary"],
                                 font=fonts.font("chart_axis"))

        for bar in lay["bars"]:
            self._draw_bar(bar, progress)

        for text, x, y, anchor in lay["labels"]:
            self.create_text(x, y, text=text, anchor=anchor,
                             fill=pal["secondary"], font=fonts.font("chart_axis"))

    def _draw_bar(self, bar, p):
        """Рисует один столбец диаграммы."""
        x0, y0, x1, y1 = bar["x0"], bar["y0"], bar["x1"], bar["y1"]
        if bar["grow"] == "up":
            # вертикальный столбец «растёт» снизу вверх по прогрессу p
            y0 = y1 - (y1 - y0) * p
            vx, vy, vanchor = (x0 + x1) / 2, y0 - 12, "s"  # подпись над столбцом
        else:
            # горизонтальный столбец «растёт» слева направо
            x1 = x0 + (x1 - x0) * p
            vx, vy, vanchor = x1 + 8, (y0 + y1) / 2, "w"   # подпись справа
        if abs(x1 - x0) < 1 or abs(y1 - y0) < 1:
            return  # столбец ещё нулевой высоты — не рисуем
        self._round_rect(x0, y0, x1, y1, self.CORNER, fill=bar["fill"])
        if p > 0.85:  # значение показываем ближе к концу анимации
            self.create_text(vx, vy, text=bar["value_text"], anchor=vanchor,
                             fill=self.pal["secondary"],
                             font=fonts.font("chart_value"))

    def _round_rect(self, x0, y0, x1, y1, r, **kw):
        """Рисует скруглённый прямоугольник на Canvas."""
        r = min(r, abs(x1 - x0) / 2, abs(y1 - y0) / 2)  # радиус не больше полстороны
        # набор точек по периметру; smooth=True сглаживает углы в скругления
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r,
               x1, y1, x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r,
               x0, y0 + r, x0, y0]
        return self.create_polygon(pts, smooth=True, **kw)


def _pil_font(role, scale):
    """Подбирает шрифт для Pillow-рендера."""
    family_size = fonts.font(role)
    size = int(family_size[1] * scale)  # масштабируем размер под разрешение
    bold = "bold" in family_size        # нужно ли жирное начертание
    # перебираем пути к подходящим шрифтам на разных ОС
    candidates = ([
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ])
    for fp in candidates:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render_image(model, pal, path, width=1280, height=800, scale=2):
    """Рендерит диаграмму в файл (PNG/PDF) средствами Pillow."""
    if not HAS_PIL:
        raise RuntimeError("Для экспорта графика установите Pillow: pip install Pillow")
    W, H = width * scale, height * scale  # рисуем крупнее, потом уменьшим (сглаживание)
    img = Image.new("RGB", (W, H), _hex_to_rgb(pal["panel"]))  # холст-фон
    d = ImageDraw.Draw(img)
    lay = build_layout(model, W, H, pal)  # та же геометрия, что и на экране

    f_title = _pil_font("chart_title", scale)
    f_axis = _pil_font("chart_axis", scale)
    f_value = _pil_font("chart_value", scale)

    d.text((lay["plot"][0], 18 * scale), lay["title"],
           fill=_hex_to_rgb(pal["fg"]), font=f_title)

    for gx0, gy0, gx1, gy1, tlabel in lay["grid"]:
        d.line((gx0, gy0, gx1, gy1), fill=_hex_to_rgb(pal["grid"]), width=scale)
        if lay["horizontal"]:
            d.text((gx0, gy1 + 8 * scale), tlabel, fill=_hex_to_rgb(pal["secondary"]),
                   font=f_axis, anchor="ma")
        else:
            d.text((lay["plot"][0] - 8 * scale, gy0), tlabel,
                   fill=_hex_to_rgb(pal["secondary"]), font=f_axis, anchor="rm")

    radius = 7 * scale
    for bar in lay["bars"]:
        box = (bar["x0"], bar["y0"], bar["x1"], bar["y1"])
        if box[2] - box[0] < 1 or box[3] - box[1] < 1:
            continue
        d.rounded_rectangle(box, radius=radius, fill=_hex_to_rgb(bar["fill"]))
        if bar["grow"] == "up":
            d.text(((box[0] + box[2]) / 2, box[1] - 10 * scale), bar["value_text"],
                   fill=_hex_to_rgb(pal["secondary"]), font=f_value, anchor="mb")
        else:
            d.text((box[2] + 6 * scale, (box[1] + box[3]) / 2), bar["value_text"],
                   fill=_hex_to_rgb(pal["secondary"]), font=f_value, anchor="lm")

    for text, x, y, anchor in lay["labels"]:
        pil_anchor = {"e": "rm", "n": "ma", "w": "lm"}.get(anchor, "mm")
        d.text((x, y), text, fill=_hex_to_rgb(pal["secondary"]),
               font=f_axis, anchor=pil_anchor)

    img = img.resize((width, height), Image.LANCZOS)  # уменьшаем для гладких краёв
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        img.save(path, "PDF", resolution=150)  # сохраняем как PDF
    else:
        img.save(path)                          # иначе обычная картинка (PNG)


class ChartWindow(tk.Toplevel):
    """Отдельное окно просмотра диаграммы выбранной модели."""
    def __init__(self, parent, model, pal, on_export=None):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(parent)
        self.model = model
        self.pal = pal
        self.on_export = on_export
        self.title(model["title"])
        self.geometry("820x560")
        self.minsize(560, 420)
        self.configure(bg=pal["bg"])

        from tkinter import ttk
        wrap = ttk.Frame(self, padding=12, style="TFrame")
        wrap.pack(fill=tk.BOTH, expand=True)

        card = tk.Frame(wrap, bg=pal["panel"], highlightthickness=1,
                        highlightbackground=pal["border"])
        card.pack(fill=tk.BOTH, expand=True)
        self.canvas = ChartCanvas(card, model, pal, width=760, height=460)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        bar = ttk.Frame(wrap)
        bar.pack(fill=tk.X, pady=(10, 0))
        if on_export:
            ttk.Button(bar, text="Сохранить PNG…", style="Accent.TButton",
                       command=on_export).pack(side=tk.LEFT)
        ttk.Button(bar, text="Закрыть", command=self.destroy).pack(side=tk.RIGHT)

        self.after(60, self.canvas.show)


class LineCanvas(tk.Canvas):
    """Лёгкий линейный график для числового столбца."""

    def __init__(self, master, pal, **kw):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(master, highlightthickness=0, bd=0,
                         bg=pal["glass"], **kw)
        self.pal = pal
        self.points = []
        self.title = ""
        self.bind("<Configure>", lambda _event: self.redraw())

    def set_data(self, title, values):
        """Передаёт данные виджету и запускает перерисовку."""
        self.title = title
        self.points = []
        # собираем только числовые значения как пары (номер, число)
        for i, value in enumerate(values, start=1):
            if str(value).strip() and _is_chart_number(value):
                num = float(str(value).replace(",", ".").replace(" ", ""))
                self.points.append((i, num))
        self.redraw()

    def redraw(self):
        """Перерисовывает содержимое canvas."""
        self.delete("all")
        w = self.winfo_width() or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        pal = self.pal
        self.create_text(28, 26, text=self.title, anchor="w",
                         fill=pal["fg"], font=fonts.font("chart_title"))
        if len(self.points) < 2:
            # линию по одной точке не построить
            self.create_text(w / 2, h / 2, text="Недостаточно числовых данных",
                             fill=pal["secondary"], font=fonts.font("body"))
            return

        x0, y0, x1, y1 = 56, 74, w - 32, h - 58  # границы области графика
        values = [p[1] for p in self.points]
        lo, hi = min(values), max(values)
        if lo == hi:
            # все значения равны — раздвигаем диапазон, чтобы линия не слиплась
            lo -= 1
            hi += 1
        for i in range(5):  # 5 горизонтальных линий сетки с подписями
            y = y1 - (y1 - y0) * i / 4
            self.create_line(x0, y, x1, y, fill=pal["grid"])
            label = lo + (hi - lo) * i / 4
            self.create_text(x0 - 10, y, text=f"{label:g}", anchor="e",
                             fill=pal["secondary"], font=fonts.font("chart_axis"))
        self.create_line(x0, y1, x1, y1, fill=pal["border"])

        n = len(self.points)
        coords = []
        # переводим каждую точку (номер, значение) в координаты пикселей
        for pos, value in self.points:
            x = x0 + (x1 - x0) * ((pos - 1) / max(1, n - 1))
            y = y1 - (y1 - y0) * ((value - lo) / (hi - lo))
            coords.extend([x, y])
        # сама линия графика со скруглёнными стыками
        self.create_line(*coords, fill=pal["accent"], width=2,
                         capstyle=tk.ROUND, joinstyle=tk.ROUND)
        # точки-маркеры поверх линии (coords чередует x и y)
        for i, (x, y) in enumerate(zip(coords[::2], coords[1::2]), start=1):
            self.create_oval(x - 4, y - 4, x + 4, y + 4,
                             fill=pal["panel"], outline=pal["accent"], width=2)
            if n <= 12:
                self.create_text(x, y1 + 18, text=str(i), anchor="n",
                                 fill=pal["secondary"],
                                 font=fonts.font("chart_axis"))


class QualityCanvas(tk.Canvas):
    """Сводка качества данных: полнота, ошибки, структура."""

    def __init__(self, master, pal, **kw):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(master, highlightthickness=0, bd=0,
                         bg=pal["glass"], **kw)
        self.pal = pal
        self.stats = {}
        self.bind("<Configure>", lambda _event: self.redraw())

    def set_data(self, project, bad_cells):
        """Передаёт данные виджету и запускает перерисовку."""
        total = len(project.rows) * len(project.columns)  # всего ячеек
        bad = len(bad_cells)                                # проблемных ячеек
        empty = 0
        # отдельно считаем пустые ячейки
        for row in project.rows:
            for ci in range(len(project.columns)):
                if ci >= len(row) or str(row[ci]).strip() == "":
                    empty += 1
        ok = max(0, total - bad)  # корректные ячейки
        self.stats = {
            "rows": len(project.rows),
            "cols": len(project.columns),
            "total": total,
            "bad": bad,
            "empty": empty,
            "ok": ok,
            "quality": 0 if total == 0 else ok / total,
        }
        self.redraw()

    def redraw(self):
        """Перерисовывает содержимое canvas."""
        self.delete("all")
        w = self.winfo_width() or int(self["width"])
        pal = self.pal
        self.create_text(28, 26, text="Качество данных", anchor="w",
                         fill=pal["fg"], font=fonts.font("chart_title"))
        if not self.stats:
            return
        quality = self.stats["quality"]      # доля корректных ячеек (0..1)
        percent = int(quality * 100)
        self.create_text(28, 70, text=f"{percent}% корректных ячеек",
                         anchor="w", fill=pal["fg"], font=fonts.font("metric"))
        bx0, by0, bx1, by1 = 28, 112, w - 28, 132  # полоса-индикатор качества
        # серый фон полосы
        self.create_rectangle(bx0, by0, bx1, by1, fill=pal["border_soft"],
                              outline=pal["border_soft"])
        # заполненная часть: зелёная при 100%, иначе янтарная
        self.create_rectangle(bx0, by0, bx0 + (bx1 - bx0) * quality, by1,
                              fill=pal["success"] if quality == 1 else pal["warning"],
                              outline="")
        cards = [
            ("Строк", self.stats["rows"], pal["fg"]),
            ("Столбцов", self.stats["cols"], pal["fg"]),
            ("Проблемных ячеек", self.stats["bad"], pal["danger"]),
            ("Пустых ячеек", self.stats["empty"], pal["secondary"]),
        ]
        y = 176
        for title, value, color in cards:
            self.create_text(36, y, text=title, anchor="w",
                             fill=pal["secondary"], font=fonts.font("small"))
            self.create_text(w - 42, y, text=str(value), anchor="e",
                             fill=color, font=fonts.font("heading"))
            self.create_line(28, y + 26, w - 28, y + 26, fill=pal["grid"])
            y += 54


def _is_chart_number(value):
    """Проверяет числовое значение для графика."""
    try:
        float(str(value).replace(",", ".").replace(" ", ""))
        return True
    except (TypeError, ValueError):
        return False


class StatisticsWindow(tk.Toplevel):
    """Единое окно статистики: график, диаграмма и качество данных."""

    def __init__(
        self,
        parent,
        project,
        pal,
        bad_cells,
        initial_column=None,
        on_column_change=None,
    ):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        super().__init__(parent)
        self.project = project
        self.pal = pal
        self.bad_cells = bad_cells
        self.on_column_change = on_column_change
        self.title("Статистика")
        self.geometry("920x620")
        self.minsize(700, 500)
        self.configure(bg=pal["bg"])

        from tkinter import ttk
        wrap = ttk.Frame(self, padding=16, style="App.TFrame")
        wrap.pack(fill=tk.BOTH, expand=True)

        top = tk.Frame(wrap, bg=pal["bg"], bd=0)
        top.pack(fill=tk.X, pady=(0, 12))
        tk.Label(top, text="Статистика", bg=pal["bg"], fg=pal["fg"],
                 font=fonts.font("title")).pack(side=tk.LEFT)

        self.column_var = tk.StringVar(value=self._initial_column(initial_column))
        self.mode_var = tk.StringVar(value="График")
        self.column_combo = ttk.Combobox(
            top,
            textvariable=self.column_var,
            values=project.columns,
            state="readonly",
            width=24,
        )
        self.column_combo.pack(side=tk.RIGHT)
        self.column_combo.bind("<<ComboboxSelected>>", lambda _e: self.redraw())

        modes = tk.Frame(wrap, bg=pal["bg"], bd=0)
        modes.pack(fill=tk.X, pady=(0, 12))
        for mode in ("График", "Диаграмма", "Качество"):
            ttk.Button(modes, text=mode, command=lambda m=mode: self.set_mode(m),
                       style="Ghost.TButton").pack(side=tk.LEFT, padx=(0, 8))

        card = tk.Frame(wrap, bg=pal["glass"], highlightthickness=1,
                        highlightbackground=pal["border"])
        card.pack(fill=tk.BOTH, expand=True)

        self.line = LineCanvas(card, pal, width=840, height=460)
        self.chart = ChartCanvas(card, {
            "title": "Диаграмма",
            "series": [],
            "orientation": "horizontal",
            "x_label": "",
            "y_label": "",
        }, pal, width=840, height=460)
        self.quality = QualityCanvas(card, pal, width=840, height=460)
        self.redraw()

    def _initial_column(self, preferred):
        """Возвращает последний выбранный столбец или лучший доступный вариант."""
        if preferred in self.project.columns:
            return preferred
        return self._default_column()

    def _default_column(self):
        """Выбирает начальный столбец для статистики."""
        # предпочитаем столбец с числами — по нему графики информативнее
        for ci, column in enumerate(self.project.columns):
            values = [row[ci] if ci < len(row) else "" for row in self.project.rows]
            numeric = [v for v in values if _is_chart_number(v) and str(v).strip()]
            if len(numeric) >= 2:
                return column
        return self.project.columns[0] if self.project.columns else ""

    def set_mode(self, mode):
        """Переключает режим статистического окна."""
        self.mode_var.set(mode)
        self.redraw()

    def _values(self):
        """Возвращает значения выбранного столбца."""
        if self.column_var.get() not in self.project.columns:
            return []
        ci = self.project.columns.index(self.column_var.get())
        return [row[ci] if ci < len(row) else "" for row in self.project.rows]

    def redraw(self):
        """Перерисовывает содержимое canvas."""
        # прячем все три холста, показываем только нужный по режиму
        for widget in (self.line, self.chart, self.quality):
            widget.pack_forget()
        mode = self.mode_var.get()
        column = self.column_var.get()
        values = self._values()
        if column and self.on_column_change:
            self.on_column_change(column)  # сообщаем окну о выбранном столбце
        if mode == "График":
            self.line.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            self.line.set_data(f"График значений · {column}", values)
        elif mode == "Диаграмма":
            self.chart.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            self.chart.model = build_model(column, values, _is_chart_number)
            self.chart.show()  # с анимацией появления
        else:  # режим «Качество»
            self.quality.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            self.quality.set_data(self.project, self.bad_cells)

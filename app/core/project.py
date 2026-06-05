# -*- coding: utf-8 -*-
"""Модель проекта анализа: хранение данных, загрузка файлов, операции."""

import os
import csv
import json
import codecs
import hashlib
import datetime


class AnalysisProject:
    """Хранит загруженные данные, метаданные и операции над ними."""

    def __init__(self):
        """Инициализирует объект и подготавливает его внутреннее состояние."""
        self.columns = []          # список имён столбцов
        self.rows = []             # список строк (каждая — список значений)
        self.meta = self._empty_meta("Новый проект")  # описание проекта/файла

    @staticmethod
    def _empty_meta(name, author="", description=""):
        """Создаёт пустой словарь метаданных проекта."""
        return {
            "name": name or "Новый проект",
            "author": author,
            # дата создания фиксируется в момент вызова
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": description,
            "source_file": "",   # путь к открытому файлу (пусто, пока не загружен)
            "file_format": "",   # TXT / CSV / JSON
            "encoding": "",      # определённая кодировка
            "file_size": "",     # человекочитаемый размер
            "md5": "",           # контрольная сумма содержимого
        }

    def reset(self, name="Новый проект", author="", description=""):
        """Сбрасывает проект к пустому состоянию."""
        self.columns = []
        self.rows = []
        self.meta = self._empty_meta(name, author, description)

    @staticmethod
    def detect_encoding(path):
        """Определяет наиболее вероятную кодировку файла."""
        # читаем первые байты — по BOM можно сразу узнать кодировку
        with open(path, "rb") as f:
            raw = f.read(4)
        if raw.startswith(codecs.BOM_UTF8):
            return "utf-8-sig"
        if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
            return "utf-16"
        # BOM нет — пробуем кодировки по очереди, пока файл не прочитается
        for enc in ("utf-8", "cp1251", "latin-1"):
            try:
                with open(path, "r", encoding=enc) as f:
                    f.read()
                return enc
            except (UnicodeDecodeError, UnicodeError):
                continue
        return "utf-8"  # запасной вариант

    @staticmethod
    def _file_info(path):
        """Возвращает размер файла и MD5-хеш."""
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        return size, md5

    def _set_common_meta(self, path, fmt, encoding):
        """Заполняет общие метаданные после загрузки файла."""
        size, md5 = self._file_info(path)
        self.meta["source_file"] = path
        self.meta["file_format"] = fmt
        self.meta["encoding"] = encoding
        self.meta["file_size"] = self._human_size(size)
        self.meta["md5"] = md5
        # если имя проекта по умолчанию — подставляем имя файла
        if not self.meta.get("name") or self.meta["name"] == "Новый проект":
            self.meta["name"] = os.path.basename(path)

    @staticmethod
    def _human_size(num):
        """Форматирует размер файла в человекочитаемый вид."""
        # последовательно делим на 1024, пока число не станет «небольшим»
        for unit in ("Б", "КБ", "МБ", "ГБ"):
            if num < 1024:
                # байты показываем без дробной части, остальное — с одним знаком
                return f"{num:.0f} {unit}" if unit == "Б" else f"{num:.1f} {unit}"
            num /= 1024
        return f"{num:.1f} ТБ"

    def load_txt(self, path):
        """Загружает TXT как таблицу строк."""
        enc = self.detect_encoding(path)
        with open(path, "r", encoding=enc) as f:
            lines = f.read().splitlines()
        # текстовый файл показываем как две колонки: номер и содержимое строки
        self.columns = ["№", "Содержимое строки"]
        self.rows = [[str(i + 1), line] for i, line in enumerate(lines)]
        self._set_common_meta(path, "TXT", enc)

    def load_csv(self, path):
        """Загружает CSV с автоопределением разделителя."""
        enc = self.detect_encoding(path)
        with open(path, "r", encoding=enc, newline="") as f:
            sample = f.read(4096)  # фрагмент для анализа разделителя
            f.seek(0)
            try:
                # Sniffer сам определяет разделитель из набора кандидатов
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel  # не вышло — берём стандартный (запятая)
            reader = csv.reader(f, dialect)
            data = list(reader)
        if not data:
            self.columns, self.rows = [], []
        else:
            # первая строка — заголовки (пустые заменяем на «Столбец N»)
            self.columns = [c.strip() or f"Столбец {i+1}"
                            for i, c in enumerate(data[0])]
            self.rows = [self._fit_row(r) for r in data[1:]]
        self._set_common_meta(path, "CSV", enc)

    def load_json(self, path):
        """Загружает JSON и приводит его к табличному виду."""
        enc = self.detect_encoding(path)
        with open(path, "r", encoding=enc) as f:
            obj = json.load(f)
        self.columns, self.rows = self._json_to_table(obj)
        self._set_common_meta(path, "JSON", enc)

    def _json_to_table(self, obj):
        """Преобразует JSON-структуру в столбцы и строки."""
        if isinstance(obj, list):
            # список словарей -> столбцы из объединения всех ключей
            if obj and all(isinstance(x, dict) for x in obj):
                cols = []
                for d in obj:
                    for k in d.keys():
                        if k not in cols:  # сохраняем порядок появления ключей
                            cols.append(k)
                rows = [[self._stringify(d.get(c, "")) for c in cols]
                        for d in obj]
                return cols, rows
            # просто список значений -> один столбец
            return ["Значение"], [[self._stringify(x)] for x in obj]
        if isinstance(obj, dict):
            # словарь -> две колонки «ключ / значение»
            return ["Ключ", "Значение"], \
                   [[str(k), self._stringify(v)] for k, v in obj.items()]
        # одиночное значение
        return ["Значение"], [[self._stringify(obj)]]

    @staticmethod
    def _stringify(v):
        """Преобразует значение в безопасное строковое представление."""
        if isinstance(v, (dict, list)):
            # вложенные структуры сериализуем обратно в JSON-строку
            return json.dumps(v, ensure_ascii=False)
        if v is None:
            return ""
        return str(v)

    def _fit_row(self, row):
        """Подгоняет длину строки под число столбцов."""
        n = len(self.columns)
        row = list(row)
        if len(row) < n:
            row += [""] * (n - len(row))  # не хватает ячеек — дополняем пустыми
        elif len(row) > n:
            row = row[:n]                 # лишние ячейки отбрасываем
        return row

    def sort_by(self, col_index, descending=False):
        """Сортирует строки с учётом числовых и текстовых значений."""
        def key(row):
            """Возвращает ключ сортировки для значения ячейки."""
            val = row[col_index] if col_index < len(row) else ""
            try:
                # числа идут группой 0 и сравниваются как числа
                return (0, float(str(val).replace(",", ".")))
            except (ValueError, TypeError):
                # текст идёт группой 1 и сравнивается по алфавиту
                return (1, str(val).lower())
        self.rows.sort(key=key, reverse=descending)

    def add_row(self):
        """Добавляет пустую строку в текущую таблицу."""
        self.rows.append(["" for _ in self.columns])

    def delete_rows(self, indices):
        """Удаляет строки по индексам."""
        # удаляем с конца, чтобы индексы не «съезжали» при удалении
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(self.rows):
                del self.rows[i]

    def add_column(self, name):
        """Добавляет столбец и пустые значения во все строки."""
        self.columns.append(name)
        for r in self.rows:
            r.append("")  # каждой строке — новая пустая ячейка

    def validate_detail(self):
        """Возвращает строки, ячейки и сообщения с результатом проверки."""
        bad_rows = set()
        bad_cells = set()
        messages = []
        ncols = len(self.columns)

        # --- шаг 1: определяем, какие столбцы считать числовыми ---
        numeric_cols = set()
        for ci in range(ncols):
            total = nums = 0
            for r in self.rows:
                v = r[ci] if ci < len(r) else ""
                if str(v).strip() == "":
                    continue  # пустые в подсчёте не участвуют
                total += 1
                if self._is_number(v):
                    nums += 1
            # столбец числовой, если ≥3 значений и больше 60% из них — числа
            if total >= 3 and nums / total > 0.6:
                numeric_cols.add(ci)

        # --- шаг 2: ищем проблемные строки и ячейки ---
        for ri, r in enumerate(self.rows):
            if len(r) != ncols:  # неверное число ячеек в строке
                bad_rows.add(ri)
                for ci in range(ncols):
                    if ci >= len(r):
                        bad_cells.add((ri, ci))  # недостающие ячейки
            for ci in range(min(len(r), ncols)):
                v = str(r[ci]).strip()
                if v == "":  # пустая ячейка
                    bad_rows.add(ri)
                    bad_cells.add((ri, ci))
                elif ci in numeric_cols and not self._is_number(r[ci]):
                    # в числовом столбце оказался текст
                    bad_rows.add(ri)
                    bad_cells.add((ri, ci))

        # --- шаг 3: человекочитаемые сообщения ---
        if bad_rows:
            messages.append(f"Найдено строк с ошибками: {len(bad_rows)}")
        else:
            messages.append("Ошибок не обнаружено.")
        if numeric_cols:
            names = ", ".join(self.columns[c] for c in sorted(numeric_cols))
            messages.append(f"Числовые столбцы: {names}")
        return bad_rows, bad_cells, messages

    def validate(self):
        """Возвращает множество индексов строк с ошибками и список сообщений."""
        # упрощённая версия validate_detail без информации о ячейках
        bad_rows, _bad_cells, messages = self.validate_detail()
        return bad_rows, messages

    @staticmethod
    def _is_number(v):
        """Проверяет, можно ли значение трактовать как число."""
        try:
            # допускаем запятую как разделитель и пробелы-разделители разрядов
            float(str(v).replace(",", ".").replace(" ", ""))
            return True
        except (ValueError, TypeError):
            return False

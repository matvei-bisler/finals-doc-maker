"""Общие утилиты для всех генераторов: доступ к Google Sheets, Typst-хелперы, даты.

Ничего не пишет на диск, кроме временного .typ-файла на время компиляции —
все PDF возвращаются как bytes, чтобы Streamlit мог отдавать их через download_button.
"""
from __future__ import annotations

import csv
import io
import os
import re
import tempfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import requests
import typst

# ---- Google Sheets ----
DEFAULT_SPREADSHEET_ID = "1bvZ4C-3Mf7-sRmpL7F1N_xUT4NfXzDPNicLGOQ1_a7M"

SHEET_STUDENTS = "2025/26"
SHEET_GEK = "ГЭК"
SHEET_SCHEDULE = "График"
SHEET_REGISTRY = "Реестр файлов"

# ---- Ассеты (pics/, fonts/ лежат в корне репозитория, рядом с logic/) ----
_THIS_DIR = Path(__file__).resolve().parent
APP_DIR = _THIS_DIR.parent
ASSETS_ROOT = APP_DIR
FONT_PATHS = [str(ASSETS_ROOT / "fonts")]


def sheet_url(spreadsheet_id: str = DEFAULT_SPREADSHEET_ID, sheet_name: str | None = None) -> str:
    """Ссылка на Google-таблицу (общая или на конкретный лист по имени — просто откроет книгу)."""
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def fetch_sheet_rows(sheet_name: str, spreadsheet_id: str = DEFAULT_SPREADSHEET_ID) -> list[dict]:
    """Скачивает лист Google Таблицы как CSV и возвращает список строк (dict)."""
    url = (f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
           f"/gviz/tq?tqx=out:csv&sheet={requests.utils.quote(sheet_name)}")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.text)))


def fetch_csv_matrix(spreadsheet_id: str, sheet_name: str | None = None) -> list[list[str]]:
    """Скачивает лист (или первый лист) как матрицу строк — для файлов отзывов/рецензий."""
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv"
    if sheet_name:
        url += "&sheet=" + requests.utils.quote(sheet_name)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return list(csv.reader(io.StringIO(r.text)))


def matrix_to_dicts(matrix: list[list[str]]) -> list[dict]:
    if not matrix:
        return []
    headers = [h.strip() for h in matrix[0]]
    return [dict(zip(headers, row)) for row in matrix[1:]]


def g(row: dict, key: str) -> str:
    return (row.get(key) or "").strip()


def truthy(v) -> bool:
    return (v or "").strip().lower() in ("true", "1", "да", "yes", "истина", "x", "✓")


def escape_typst(s) -> str:
    """Экранирует спецсимволы для Typst content-блоков [...]"""
    if s is None:
        return ""
    return (
        str(s)
        .replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("@", "\\@")
        .replace("$", "\\$")
        .replace("_", "\\_")
        .replace("*", "\\*")
    )


def sanitize_filename(s) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", str(s)).strip()


# ---- Даты (родительный падеж, как принято в приказах) ----
MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}
MONTH_NAME_TO_NUM = {v: k for k, v in MONTHS_RU.items()}


def format_date_ru(dt: datetime | date) -> str:
    return f"«{dt.day:02d}» {MONTHS_RU[dt.month]} {dt.year} года"


def date_to_order_string(d: date) -> str:
    """st.date_input -> «22» апреля 2026 года (для полей ORDER_DATE)."""
    return format_date_ru(d)


def parse_gsheet_date(s: str):
    """gviz отдаёт даты вида 'Monday, 8 June 2026'. Возвращает datetime или None."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%A, %d %B %Y", "%d %B %Y", "%d.%m.%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def order_num_from_date(order_date_str: str, seq: int) -> str:
    """№ приказа из даты: «18» марта 2026 года → 18032026-{seq}."""
    m = re.search(r"(\d{1,2})[^0-9а-яё]+([а-яё]+)[^0-9а-яё]+(\d{4})", order_date_str.lower())
    if m and m.group(2) in MONTH_NAME_TO_NUM:
        d, mo, y = int(m.group(1)), MONTH_NAME_TO_NUM[m.group(2)], int(m.group(3))
        return f"{d:02d}{mo:02d}{y}-{seq}"
    return f"________-{seq}"


# ---- Разбор оценок (поддерживает и слова, и цифры) ----
WORD_TO_GRADE = {"отлично": 5, "хорошо": 4, "удовлетворительно": 3, "неудовлетворительно": 2}
GRADE_WORD = {v: k for k, v in WORD_TO_GRADE.items()}


def parse_grade(value: str):
    v = (value or "").strip().lower()
    if not v:
        return None
    if v in WORD_TO_GRADE:
        return WORD_TO_GRADE[v]
    try:
        n = int(float(v.replace(",", ".")))
        return n if 2 <= n <= 5 else None
    except ValueError:
        return None


def parse_year(value) -> int:
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


# ---- Фильтрация по факультету/направлению/программе (для «сгенерировать индивидуально») ----
def matches_filter(
    r: dict,
    faculties: list[str] | None = None,
    directions: list[str] | None = None,
    programs: list[str] | None = None,
) -> bool:
    """Пустой список/None в любом из фильтров = не фильтровать по этому измерению."""
    if faculties and g(r, "факультет") not in faculties:
        return False
    if directions and g(r, "направление") not in directions:
        return False
    if programs and g(r, "программа") not in programs:
        return False
    return True


def filter_students(
    rows: list[dict],
    faculties: list[str] | None = None,
    directions: list[str] | None = None,
    programs: list[str] | None = None,
) -> list[dict]:
    return [r for r in rows if matches_filter(r, faculties, directions, programs)]


def unique_facets(rows: list[dict]) -> dict[str, list[str]]:
    """Списки уникальных факультетов/направлений/программ (только строки с заполненным ФИО)."""
    live = [r for r in rows if g(r, "ФИО")]
    return {
        "faculties": sorted({g(r, "факультет") for r in live if g(r, "факультет")}),
        "directions": sorted({g(r, "направление") for r in live if g(r, "направление")}),
        "programs": sorted({g(r, "программа") for r in live if g(r, "программа")}),
    }


# ---- Typst → PDF bytes (без временных файлов на диске в выходной папке) ----
# Typst требует, чтобы входной .typ-файл лежал ВНУТРИ --root, иначе "input file must be
# contained in project root" — поэтому временный файл создаётся не в системном /tmp,
# а в скрытой подпапке внутри ASSETS_ROOT.
_TMP_DIR = ASSETS_ROOT / ".streamlit_tmp"


def compile_typst(doc_text: str) -> bytes:
    """Компилирует .typ-текст в PDF-байты. root=корень репозитория, чтобы работали /pics/... и шрифты."""
    _TMP_DIR.mkdir(exist_ok=True)
    fd, temp_path = tempfile.mkstemp(suffix=".typ", dir=str(_TMP_DIR))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(doc_text)
        return typst.compile(temp_path, root=str(ASSETS_ROOT), font_paths=FONT_PATHS)
    finally:
        os.remove(temp_path)


MINOBR_PREAMBLE = (
    "В соответствии с приказом Минобрнауки России от 29 июня 2015 г. № 636 "
    "«Об утверждении Порядка проведения государственной итоговой аттестации по "
    "образовательным программам высшего образования – программам бакалавриата, "
    "программам специалитета, программам магистратуры»\n"
    "#v(0.5em)\n#align(left)[приказываю:]"
)


def build_prikaz_header(order_num: str, order_date: str, subtitle: str,
                         preamble: str = MINOBR_PREAMBLE) -> str:
    """Общая шапка приказов ГЭК/расписание/апелляция (стиль generate_prikaz)."""
    return (
        '#set page(paper: "a4", margin: (top: 1.5cm, bottom: 2cm, left: 2.5cm, right: 1.5cm))\n'
        '#set text(size: 11pt, lang: "ru", font: "Times New Roman")\n'
        '#set par(justify: true, leading: 1em, spacing: 1em)\n'
        '#set block(spacing: 1em)\n'
        '#show table.cell: set par(leading: 0.5em, spacing: 0.3em)\n'
        '#let logo = image("/pics/logo.svg")\n'
        '#set text(size: 10pt)\n'
        '#set par(justify: false)\n'
        '#table(\n'
        '  columns: (1fr, 3fr),\n'
        '  stroke: (left: 0pt, right: 0pt, top: 0pt, bottom: 0pt),\n'
        '  column-gutter: 0.5em,\n'
        '  table.vline(x: 1, stroke: 0.5pt),\n'
        '  [#align(horizon)[#logo]],\n'
        '  [\n'
        '    #v(0.75em)\n'
        '    #text(font: "Times New Roman", size: 9pt)[#align(horizon)[\n'
        '      АНО ВО «Универсальный Университет» \\ ОГРН 1197700010518 \\ 105120, Россия, г. Москва, Центр дизайна ARTPLAY \\ ул. Нижняя Сыромятническая, д. 10, стр. 3]\n'
        '    ]\n'
        '  ],\n'
        ')\n'
        '#set text(size: 11pt)\n'
        '#set par(justify: true, leading: 1em, spacing: 1em)\n'
        '#v(1em)\n'
        f'#align(center)[*АВТОНОМНАЯ НЕКОММЕРЧЕСКАЯ ОРГАНИЗАЦИЯ ВЫСШЕГО ОБРАЗОВАНИЯ \\ «УНИВЕРСАЛЬНЫЙ УНИВЕРСИТЕТ» \\ #v(1em) ПРИКАЗ № {escape_typst(order_num)}*]\n'
        '#v(1em)\n'
        '#grid(columns: (1fr, auto),\n'
        '  [г. Москва],\n'
        f'  [{escape_typst(order_date)}],\n'
        ')\n'
        '#v(1em)\n'
        f'#align(left)[{subtitle}]\n'
        '#v(1em)\n'
        f'{preamble}\n'
        '#v(0.8em)\n'
    )


def build_prikaz_footer() -> str:
    return (
        '\n#block(breakable: false)[\n'
        '#v(3em)\n'
        '#table(\n'
        '  columns: (2fr, 1fr, 1fr),\n'
        '  stroke: none,\n'
        '  align: (left + bottom, center + bottom, left + bottom),\n'
        '  [Директор АНО ВО \\ «Универсальный университет»],\n'
        '  [#line(stroke: 0.03em, length: 100%)],\n'
        '  [А.А. Саввин],\n'
        ')\n'
        ']\n'
    )


class GenerationResult:
    """Результат работы генератора: файлы (relpath -> bytes) + лог строк для UI."""

    def __init__(self):
        self.files: dict[str, bytes] = {}
        self.log: list[str] = []
        self.errors: list[str] = []

    def add(self, relpath: str, doc_text: str):
        try:
            pdf = compile_typst(doc_text)
            self.files[relpath] = pdf
            self.log.append(f"✓ {relpath} ({len(pdf):,} байт)")
        except Exception as e:
            self.errors.append(f"✗ {relpath}: {e}")
            self.log.append(f"✗ {relpath}: {e}")

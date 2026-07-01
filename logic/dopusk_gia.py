"""Приказ(-ы) о допуске к прохождению ГИА.

Группирует обучающихся по (направление, программа), определяет период ГИА по правилам
(подстрока в названии программы → период), дата приказа — N рабочих дней до начала ГИА.
Приказы за один день объединяются и нумеруются 1,2,3... внутри дня.

Примечание: в исходном ноутбуке жёстко фильтровались только студенты 4 курса — это молча
исключало архитектуру (5 курс) и магистратуру (2 курс) из допуска. Здесь набор курсов —
явный параметр UI (по умолчанию заполняется всеми курсами, что реально есть в таблице).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from itertools import groupby

from . import common as c

# ---- Правила периодов ГИА по умолчанию: (подстрока в программе, начало, конец) ----
# Проверяются по порядку, первое совпадение побеждает (без учёта регистра).
DEFAULT_GIA_RULES: list[dict] = [
    {"keyword": "архитектура и градостроительство", "start": "08.05.2026", "end": "22.07.2026"},
    {"keyword": "проектирование зданий", "start": "28.06.2026", "end": "24.07.2026"},
    {"keyword": "дизайн", "start": "29.06.2026", "end": "26.07.2026"},
    {"keyword": "анимация", "start": "22.06.2026", "end": "19.07.2026"},
    {"keyword": "создание игр", "start": "22.06.2026", "end": "19.07.2026"},
    {"keyword": "кинопроизводство", "start": "22.06.2026", "end": "19.07.2026"},
    {"keyword": "музыка", "start": "06.07.2026", "end": "01.08.2026"},
]
DEFAULT_FALLBACK = {"start": "01.06.2026", "end": "30.06.2026"}


def get_gia_period(program: str, rules: list[dict], fallback: dict) -> tuple[str, str]:
    pl = program.lower()
    for rule in rules:
        if rule["keyword"].lower() in pl:
            return rule["start"], rule["end"]
    return fallback["start"], fallback["end"]


def _is_working_day(d: datetime) -> bool:
    return d.weekday() < 5


def _working_days_before(start: datetime, n: int) -> datetime:
    result = start
    left = n
    while left > 0:
        result -= timedelta(days=1)
        if _is_working_day(result):
            left -= 1
    return result


def _build_header(order_num: str, order_date_str: str) -> str:
    return (
        '\n#let logo = image("/pics/logo.svg")\n\n'
        '#set page(paper: "a4", margin: (top: 1.5cm, bottom: 2cm, left: 2.5cm, right: 1.5cm))\n'
        '#set text(size: 11pt, lang: "ru", font: "Times New Roman")\n'
        '#set par(justify: true, leading: 1em, spacing: 1em)\n'
        '#set block(spacing: 1em)\n'
        '#show table.cell: set par(leading: 0.5em, spacing: 0.3em)\n\n'
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
        '#set par(justify: true, leading: 1em, spacing: 1em)\n\n'
        '#v(1em)\n'
        f'#align(center)[*АВТОНОМНАЯ НЕКОММЕРЧЕСКАЯ ОРГАНИЗАЦИЯ ВЫСШЕГО ОБРАЗОВАНИЯ \\ «УНИВЕРСАЛЬНЫЙ УНИВЕРСИТЕТ» \\ #v(1em) ПРИКАЗ № {c.escape_typst(order_num)}*]\n'
        '#v(1em)\n'
        '#grid(\n'
        '  columns: (1fr, auto),\n'
        '  [г. Москва],\n'
        f'  [{c.escape_typst(order_date_str)}],\n'
        ')\n'
        '#v(1em)\n'
        '#align(left)[О допуске к прохождению государственной итоговой аттестации]\n\n'
        '#v(1em)\n'
        '*Допустить*\n\n'
        '#v(1em)\n'
    )


def _build_footer() -> str:
    return (
        '\n#block(breakable: false)[\n'
        '#v(1em)\n'
        'Основание: ведомости текущего контроля успеваемости и промежуточной аттестации.\n\n'
        '#v(2em)\n'
        '#table(\n'
        '  columns: (2fr, 1fr, 1fr),\n'
        '  stroke: none,\n'
        '  align: (left + bottom, center + bottom, left + bottom),\n'
        '  [Директор \\ АНО ВО «Универсальный университет»],\n'
        '  [#line(stroke: 0.03em, length: 100%)],\n'
        '  [А.А. Саввин],\n'
        ')\n'
        ']\n'
    )


def _build_body(direction: str, program: str, students: list, start_date: str, end_date: str) -> str:
    students_sorted = sorted(students, key=lambda s: c.g(s, "ФИО"))
    rows = []
    for i, s in enumerate(students_sorted, 1):
        name = c.escape_typst(c.g(s, "ФИО"))
        rows.append(f"  table.cell(align: center + top)[{i}.], [{name}],")
    rows_str = "\n".join(rows)

    return (
        f"К прохождению государственной итоговой аттестации в период "
        f"с {start_date} по {end_date} обучающихся, не имеющих академических задолженностей и "
        f"в полном объёме выполнивших учебный план/индивидуальный учебный план по направлению "
        f"подготовки {c.escape_typst(direction)}, направленность (профиль) «{c.escape_typst(program)}»:\n\n"
        f"#table(\n"
        f"  columns: (auto, 1fr),\n"
        f"  stroke: (left: 0pt, right: 0pt, top: 0pt, bottom: 0.5pt),\n"
        f"  inset: (x: 5pt, y: 4pt),\n"
        f"  align: (center + top, left + top),\n"
        f"  table.header(table.cell(align: center)[№], [ФИО]),\n"
        f"{rows_str}\n"
        f")\n\n#v(0.6em)\n"
    )


def generate(
    days_before: int = 2,
    courses: list[str] | None = None,
    rules: list[dict] | None = None,
    fallback: dict | None = None,
    faculties=None, directions=None, programs=None,
    spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID,
) -> c.GenerationResult:
    res = c.GenerationResult()
    rules = rules if rules is not None else DEFAULT_GIA_RULES
    fallback = fallback if fallback is not None else DEFAULT_FALLBACK

    all_rows = c.fetch_sheet_rows(c.SHEET_STUDENTS, spreadsheet_id)
    all_rows = c.filter_students(all_rows, faculties, directions, programs)
    res.log.append(f"✓ Загружено строк: {len(all_rows)} (лист «{c.SHEET_STUDENTS}», после фильтра)")

    groups: dict = defaultdict(list)
    for row in all_rows:
        fio = c.g(row, "ФИО")
        if not fio:
            continue
        course = c.g(row, "курс")
        if courses is not None and course not in courses:
            continue
        key = (c.g(row, "направление"), c.g(row, "программа"))
        groups[key].append(row)

    if not groups:
        res.log.append("Нет обучающихся, подходящих под выбранные курсы.")
        return res

    group_info = []
    for (direction, program), students in groups.items():
        start_date, end_date = get_gia_period(program, rules, fallback)
        start_dt = datetime.strptime(start_date, "%d.%m.%Y")
        order_date_dt = _working_days_before(start_dt, days_before)
        group_info.append({
            "direction": direction, "program": program, "students": students,
            "order_date_dt": order_date_dt, "start_date": start_date, "end_date": end_date,
        })

    group_info.sort(key=lambda x: (x["order_date_dt"], x["direction"], x["program"]))

    for order_date_dt, items in groupby(group_info, key=lambda x: x["order_date_dt"]):
        items = list(items)
        date_str = order_date_dt.strftime("%d%m%Y")
        order_date_str = c.format_date_ru(order_date_dt)
        for idx, info in enumerate(items, 1):
            order_num = f"{date_str}-{idx}"
            doc = (
                _build_header(order_num, order_date_str)
                + _build_body(info["direction"], info["program"], info["students"],
                              info["start_date"], info["end_date"])
                + _build_footer()
            )
            fname = c.sanitize_filename(
                f"Приказ о допуске к ГИА — {info['program']} — {order_date_dt.strftime('%Y-%m-%d')}.pdf"
            )
            res.add(fname, doc)
            res.log.append(f"  № {order_num}: {info['direction']} / {info['program']} "
                            f"— {len(info['students'])} чел., ГИА {info['start_date']}–{info['end_date']}")

    return res

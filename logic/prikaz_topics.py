"""Приказ об утверждении тем и руководителей ВКР.

Один PDF: пункты по (направление, программа, курс), бакалавриат по коду направления,
затем магистратура. Внутри каждого пункта — таблица ФИО / тема ВКР / руководитель.
"""
from __future__ import annotations

from collections import defaultdict

from . import common as c


def _get_edu_type(year: str) -> str:
    return "магистратуры" if int(year) == 2 else "бакалавриата"


def _build_header(order_num: str, order_date: str) -> str:
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
        f'  [{c.escape_typst(order_date)}],\n'
        ')\n'
        '#v(1em)\n'
        '#align(left)[Об утверждении тем и руководителей выпускных \\ квалификационных работ обучающихся]\n\n'
        '#v(1em)\n'
        'В соответствии с Положением об организации и проведении итоговой (государственной итоговой) '
        'аттестации обучающихся образовательных программ высшего образования в АНО ВО «Универсальный '
        'Университет» приказываю:\n\n'
        '#v(0.5em)\n'
    )


def _build_footer() -> str:
    return (
        '\n#block(breakable: false)[\n'
        '#v(1em)\n'
        'Контроль исполнения приказа возложить на руководителя группы дизайнеров образовательных '
        'программ высшего образования Маркову М.В.\n\n'
        '#v(2em)\n'
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


def _build_section(num: int, direction: str, program: str, year: str, students: list) -> str:
    edu_type = _get_edu_type(year)
    year_int = int(year)

    rows = []
    for i, s in enumerate(students, 1):
        name = c.escape_typst(c.g(s, "ФИО"))
        topic = c.escape_typst(c.g(s, "тема"))
        eng_title = c.g(s, "title")
        full_topic = topic + " / " + c.escape_typst(eng_title) if eng_title else topic
        supervisor = c.escape_typst(c.g(s, "руководитель"))
        rows.append(
            f"  table.cell(align: center + top)[{i}.], [{name}], [{full_topic}], [{supervisor}],"
        )
    rows_str = "\n".join(rows)

    return (
        f"\n{num}. Утвердить темы выпускных квалификационных работ обучающихся "
        f"{year_int} курса по образовательной программе {edu_type} "
        f"{c.escape_typst(direction)}, направленность (профиль) "
        f"«{c.escape_typst(program)}» и назначить руководителей выпускных квалификационных работ:\n\n"
        f"#table(\n"
        f"  columns: (auto, 1.5fr, 2.5fr, 2fr),\n"
        f"  stroke: 0.5pt,\n"
        f"  inset: (x: 5pt, y: 4pt),\n"
        f"  align: (center + top, left + top, left + top, left + top),\n"
        f"  table.header(\n"
        f"    table.cell(align: center)[№],\n"
        f"    [ФИО],\n"
        f"    [Тема ВКР],\n"
        f"    [Руководитель],\n"
        f"  ),\n"
        f"{rows_str}\n"
        f")\n\n#v(0.6em)\n"
    )


def generate(order_num: str, order_date: str, faculties=None, directions=None, programs=None,
            spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID) -> c.GenerationResult:
    res = c.GenerationResult()
    all_rows = c.fetch_sheet_rows(c.SHEET_STUDENTS, spreadsheet_id)
    all_rows = c.filter_students(all_rows, faculties, directions, programs)
    res.log.append(f"✓ Загружено строк: {len(all_rows)} (лист «{c.SHEET_STUDENTS}», после фильтра)")

    groups: dict = defaultdict(list)
    for row in all_rows:
        if not c.g(row, "ФИО"):
            continue
        key = (c.g(row, "направление"), c.g(row, "программа"), c.g(row, "курс"))
        groups[key].append(row)

    def sort_key(item):
        (direction, program, year), _ = item
        is_master = 1 if int(year) == 2 else 0
        return (is_master, direction, program)

    sorted_groups = sorted(groups.items(), key=sort_key)

    sections = []
    for num, ((direction, program, year), students) in enumerate(sorted_groups, 1):
        students.sort(key=lambda s: c.g(s, "ФИО"))
        sections.append(_build_section(num, direction, program, year, students))
        res.log.append(f"  {num}. {direction} / {program} ({year} курс) — {len(students)} чел.")

    doc = _build_header(order_num, order_date) + "\n".join(sections) + _build_footer()
    res.add("Приказ об утверждении тем и руководителей ВКР.pdf", doc)
    return res

"""Приказ об утверждении расписания ГИА — отдельный файл на каждое направление.

Тело статично (2 пункта), приложение-расписание строится из «2025/26» (кол-во студентов)
и «График» (даты защиты, этап начинается с «защита»; аудитория — колонка «примечание»).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from . import common as c

SUBTITLE = "Об утверждении расписания государственных \\ аттестационных испытаний"

BODY1 = ("Утвердить расписание государственных аттестационных испытаний по образовательным "
         "программам высшего образования в соответствии с приложением.")
BODY2 = ("Руководителю учебного отдела Бураковой А.Д. довести утвержденное расписание до сведения "
         "обучающихся, председателей и членов государственных экзаменационных комиссий и "
         "апелляционных комиссий, секретарей государственных экзаменационных комиссий, руководителей "
         "и консультантов выпускных квалификационных работ в течение 10 рабочих дней с даты издания "
         "настоящего приказа.")


def _appendix_table(rows_cells: list[str]) -> str:
    return ("#table(\n"
            "  columns: (1.5fr, 1.7fr, 0.6fr, 1.3fr, 1.4fr),\n"
            "  stroke: 0.5pt,\n  inset: 4pt,\n  align: left + top,\n"
            "  table.header([Направление подготовки], [Направленность (профиль)], [Кол-во студ.], "
            "[Дата и время проведения], [Аудитория]),\n"
            + "\n".join(rows_cells) + "\n)\n")


def generate(order_date: str, order_num_start: int = 1, sheet_schedule: str = c.SHEET_SCHEDULE,
             faculties=None, directions=None, programs=None,
             spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID) -> c.GenerationResult:
    res = c.GenerationResult()
    students = c.fetch_sheet_rows(c.SHEET_STUDENTS, spreadsheet_id)
    students = c.filter_students(students, faculties, directions, programs)
    sched_rows = c.fetch_sheet_rows(sheet_schedule, spreadsheet_id)
    res.log.append(f"✓ Лист «{c.SHEET_STUDENTS}»: строк {len(students)}")
    res.log.append(f"✓ Лист «{sheet_schedule}»: строк {len(sched_rows)}")

    by_napr, cnt, seen = defaultdict(list), defaultdict(int), set()
    for r in students:
        if not c.g(r, "ФИО"):
            continue
        napr, prog, fac = c.g(r, "направление"), c.g(r, "программа"), c.g(r, "факультет")
        cnt[(napr, prog)] += 1
        if (napr, prog) not in seen:
            seen.add((napr, prog))
            by_napr[napr].append((prog, fac))

    sched = defaultdict(list)
    for r in sched_rows:
        if c.g(r, "этап").lower().startswith("защита"):
            sched[(c.g(r, "факультет"), c.g(r, "программа"))].append(
                (c.parse_gsheet_date(c.g(r, "дата")), c.g(r, "примечание")))

    for idx, napr in enumerate(sorted(by_napr)):
        onum = c.order_num_from_date(order_date, order_num_start + idx)
        cells = []
        for prog, fac in sorted(by_napr[napr], key=lambda x: x[0]):
            sc = sorted(sched.get((fac, prog), []), key=lambda x: (x[0] or datetime.max))
            dates = " \\\n".join(c.format_date_ru(dt) for dt, _ in sc if dt) or "—"
            auds = " \\\n".join(c.escape_typst(a) for _, a in sc if a) or "—"
            cells.append(f"  [{c.escape_typst(napr)}], [{c.escape_typst(prog)}], "
                         f"[#align(center)[{cnt[(napr, prog)]}]], [{dates}], [{auds}],")
        appendix = (
            "#pagebreak()\n#set par(justify: false)\n"
            f"#align(right)[Приложение \\ к приказу от {c.escape_typst(order_date)} № {c.escape_typst(onum)}]\n"
            "#v(1em)\n#align(center)[*РАСПИСАНИЕ \\ ГОСУДАРСТВЕННЫХ АТТЕСТАЦИОННЫХ ИСПЫТАНИЙ*]\n"
            "#v(1em)\n#set text(size: 9pt)\n" + _appendix_table(cells)
        )
        doc = (c.build_prikaz_header(onum, order_date, SUBTITLE)
               + f"1. {BODY1}\n#v(0.3em)\n2. {BODY2}\n"
               + c.build_prikaz_footer() + appendix)
        fname = c.sanitize_filename(f"Приказ о расписании ГИА — {napr}.pdf")
        res.add(fname, doc)
        res.log.append(f"  № {onum}: {napr} — программ: {len(by_napr[napr])}")

    return res

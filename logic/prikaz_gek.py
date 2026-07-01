"""Приказ об утверждении состава и секретарей ГЭК — отдельный файл на каждое направление.

Состав берётся из листа «ГЭК» (председатель/секретарь — флаги, остальные — члены).
Направление и уровень (бакалавриат/магистратура) — из листа «2025/26» по факультету+программе.
Номер приказа выводится из даты подписания (общей для всех) + порядковый номер направления.
"""
from __future__ import annotations

from collections import defaultdict

from . import common as c

SUBTITLE = "Об утверждении состава и секретарей государственных \\ экзаменационных комиссий на 2026 год"


def _level_word(kurs: str) -> str:
    return "магистратуры" if str(kurs).strip() == "2" else "бакалавриата"


def _person_line(label: str, p) -> str:
    if not p:
        return f"{label} —"
    return f"{label} {c.escape_typst(p[0])}, {c.escape_typst(p[1])}" if p[1] else f"{label} {c.escape_typst(p[0])}"


def _committee_block(chair, members, secretary) -> str:
    lines = [_person_line("Председатель:", chair)]
    if members:
        lines.append("Члены ГЭК:")
        lines += [f"{c.escape_typst(m[0])}, {c.escape_typst(m[1])}" if m[1] else c.escape_typst(m[0])
                  for m in members]
    else:
        lines.append("Члены ГЭК: —")
    lines.append(_person_line("Секретарь ГЭК:", secretary))
    return "#v(0.3em)\n#block[\n" + " \\\n".join(lines) + "\n]\n#v(0.8em)\n"


def generate(order_date: str, order_num_start: int = 1,
             faculties=None, directions=None, programs=None,
             spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID) -> c.GenerationResult:
    res = c.GenerationResult()
    students = c.fetch_sheet_rows(c.SHEET_STUDENTS, spreadsheet_id)
    gek = c.fetch_sheet_rows(c.SHEET_GEK, spreadsheet_id)
    res.log.append(f"✓ Лист «{c.SHEET_STUDENTS}»: строк {len(students)}")
    res.log.append(f"✓ Лист «{c.SHEET_GEK}»: строк {len(gek)}")

    meta = {}
    for r in students:
        if c.g(r, "ФИО"):
            meta[(c.g(r, "факультет"), c.g(r, "программа"))] = (c.g(r, "направление"), c.g(r, "курс"))

    groups = defaultdict(lambda: {"chair": None, "sec": None, "mem": []})
    for r in gek:
        fio, prog = c.g(r, "ФИО"), c.g(r, "программа")
        if not fio or not prog:
            continue
        key = (c.g(r, "факультет"), prog)
        p = (fio, c.g(r, "аффилиация"))
        if c.g(r, "председатель").upper() == "TRUE":
            groups[key]["chair"] = p
        elif c.g(r, "секретарь").upper() == "TRUE":
            groups[key]["sec"] = p
        else:
            groups[key]["mem"].append(p)

    def _keep(fac, prog):
        if faculties and fac not in faculties:
            return False
        if programs and prog not in programs:
            return False
        if directions:
            napr, _ = meta.get((fac, prog), ("", ""))
            if napr not in directions:
                return False
        return True

    by_napr = defaultdict(list)
    for (fac, prog), v in groups.items():
        if not _keep(fac, prog):
            continue
        napr, kurs = meta.get((fac, prog), ("", ""))
        by_napr[napr].append((prog, kurs, v))

    for idx, napr in enumerate(sorted(by_napr)):
        onum = c.order_num_from_date(order_date, order_num_start + idx)
        sections = []
        for n, (prog, kurs, v) in enumerate(sorted(by_napr[napr], key=lambda x: x[0]), 1):
            para = (f"{n}. Утвердить состав государственной экзаменационной комиссии и секретаря "
                    f"государственной экзаменационной комиссии на 2026 год по образовательной программе "
                    f"высшего образования — программе {_level_word(kurs)} {c.escape_typst(napr)}, "
                    f"направленность (профиль) {c.escape_typst(prog)}:")
            sections.append(para + "\n" + _committee_block(v["chair"], v["mem"], v["sec"]))
        doc = c.build_prikaz_header(onum, order_date, SUBTITLE) + "\n".join(sections) + c.build_prikaz_footer()
        fname = c.sanitize_filename(f"Приказ о составе ГЭК — {napr}.pdf")
        res.add(fname, doc)
        res.log.append(f"  № {onum}: {napr} — программ: {len(by_napr[napr])}")

    return res

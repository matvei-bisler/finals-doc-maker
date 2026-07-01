"""Отчёт председателя ГЭК — отдельный PDF на каждую образовательную программу.

Результаты защиты (таблица, списки с отличием/неудов/рекомендованных) строятся
из заполненных оценок в «2025/26»; выводы — обобщённый текст, подходящий под любую программу.
"""
from __future__ import annotations

from collections import defaultdict

from . import common as c

FORM_DEFAULT = "очная"


def _edu_type(kurs) -> str:
    return "магистратуры" if str(kurs).strip() == "2" else "бакалавриата"


def _pct(x: int, base: int) -> str:
    return str(round(100 * x / base)) if base else "0"


def _build_commissions(gek_rows: list[dict]) -> dict:
    by = defaultdict(lambda: {"chair": None, "sec": None, "mem": []})
    for r in gek_rows:
        fio, prog = c.g(r, "ФИО"), c.g(r, "программа")
        if not fio or not prog:
            continue
        key = (c.g(r, "факультет"), prog)
        person = (fio, c.g(r, "аффилиация"))
        if c.truthy(r.get("председатель")):
            by[key]["chair"] = person
        elif c.truthy(r.get("секретарь")):
            by[key]["sec"] = person
        else:
            by[key]["mem"].append(person)
    return by


def _person_cell(p) -> str:
    if not p:
        return "[]"
    name, aff = c.escape_typst(p[0]), c.escape_typst(p[1])
    return f"[{name}" + (f" \\ {aff}" if aff else "") + "]"


def _commission_table(comm) -> str:
    chair = comm["chair"] if comm else None
    sec = comm["sec"] if comm else None
    members = comm["mem"] if comm else []
    rows = [f"    [председатель ГЭК], {_person_cell(chair)},"]
    if members:
        rows.append(f"    [члены ГЭК], {_person_cell(members[0])},")
        for m in members[1:]:
            rows.append(f"    [], {_person_cell(m)},")
    else:
        rows.append("    [члены ГЭК], [],")
    rows.append(f"    [секретарь ГЭК], {_person_cell(sec)},")
    return "#table(\n    columns: (0.5fr, 1fr),\n    stroke: none,\n" + "\n".join(rows) + "\n  )\n"


def _short_name_typ(p) -> str:
    return f'#short-name("{c.escape_typst(p[0])}")' if p else ""


PREAMBLE = r'''#let logo = image("/pics/logo.svg")
#set page(paper: "a4")
#set text(size: 11pt, lang: "ru", font: "Times New Roman")
#set par(justify: true, spacing: 0.25em)
#set block(spacing: 0.25em)
#set heading(numbering: "1.")
#show heading.where(level: 1): set text(size: 11pt, weight: "bold")
#show heading.where(level: 1): set align(left)

#let short-name(name) = {
  let p = name.split(" ").filter(x => x != "")
  if p.len() >= 3 [#p.at(0) #p.at(1).first(). #p.at(2).first().] else [#name]
}
'''

LETTERHEAD = r'''#set text(size: 10pt, lang: "ru", font: "Times New Roman")
#set par(justify: false)
#table(
  columns: (20fr, 10fr),
  stroke: none,
  [
    #v(0.75em)
    #text(font: "Univers LT CYR", weight: 300)[
      #upper[автономная некоммерческая организация \ высшего образования]
    ]
    #v(0.75em)
    #text(font: "Univers LT CYR", weight: 700)[
      #upper["универсальный университет"]
    ]
  ],
  [#logo]
)
#set text(size: 11pt, lang: "ru", font: "Times New Roman")
#set par(justify: true, spacing: 1em)
'''


def _topic_full(s: dict) -> str:
    topic = c.escape_typst(c.g(s, "тема"))
    title = c.g(s, "title")
    return topic + (" / " + c.escape_typst(title) if title else "")


def _results_table(total, by_grade, passed, honors_n) -> str:
    def c8(cnt):
        p = _pct(cnt, total)
        return f"[{cnt}], [{p}], [{cnt}], [{p}], [\\-\\-], [\\-\\-], [\\-\\-], [\\-\\-],"
    blank8 = "[], [], [], [], [\\-\\-], [\\-\\-], [\\-\\-], [\\-\\-],"
    g5, g4, g3, g2 = (by_grade.get(k, 0) for k in (5, 4, 3, 2))
    dash = "[\\-\\-], [\\-\\-], [\\-\\-], [\\-\\-],"
    return (
        "#table(\n"
        "  columns: (0.4fr, 2fr, 0.6fr, 0.6fr, 0.6fr, 0.6fr, 0.6fr, 0.6fr, 0.6fr, 0.6fr),\n"
        "  stroke: 0.25pt,\n  align: center,\n"
        "  table.cell(rowspan: 2)[№], table.cell(rowspan: 2)[Показатели],\n"
        "  table.cell(colspan: 2)[Всего], table.cell(colspan: 2)[Очная],\n"
        "  table.cell(colspan: 2)[Очно-заочная], table.cell(colspan: 2)[Заочная],\n"
        "  [кол.], [%], [кол.], [%], [кол.], [%], [кол.], [%],\n"
        f"  [1], [Принято к защите ВКР], {c8(total)}\n"
        f"  [2], [Защищено ВКР], {c8(passed)}\n"
        f"  table.cell(rowspan: 5)[3], [Оценки за ВКР], {blank8}\n"
        f"  [отлично], {c8(g5)}\n"
        f"  [хорошо], {c8(g4)}\n"
        f"  [удовлетворительно], {c8(g3)}\n"
        f"  [неудовлетворительно], {c8(g2)}\n"
        f"  table.cell(rowspan: 4)[4], [Количество ВКР, выполненных], {blank8}\n"
        f"  [по темам, предложенным факультетом], [0], [0], [0], [0], {dash}\n"
        f"  [по темам, предложенным обучающимися], [{total}], [100], [{total}], [100], {dash}\n"
        f"  [по темам, предложенным работодателями], [0], [0], [0], [0], {dash}\n"
        f"  [5], [Количество ВКР с отличием], {c8(honors_n)}\n"
        ")\n"
    )


def _build_report(napr, prog, fac, kurs, students, comm, sessions, report_date, gek_order_num,
                  gek_order_date, form) -> str:
    et = _edu_type(kurs)
    total = len(students)
    grades = [c.parse_grade(c.g(s, "оценка")) for s in students]
    by_grade = defaultdict(int)
    for gr in grades:
        if gr:
            by_grade[gr] += 1
    passed = sum(1 for gr in grades if gr in (3, 4, 5))
    honors = [c.g(s, "ФИО") for s in students if c.truthy(s.get("диплом с отличием"))]
    unsat = [c.g(s, "ФИО") for s, gr in zip(students, grades) if gr == 2]
    excellent = [c.g(s, "ФИО") for s, gr in zip(students, grades) if gr == 5]

    napr_e, prog_e = c.escape_typst(napr), c.escape_typst(prog)
    comm_tbl = _commission_table(comm)
    chair = comm["chair"] if comm else None

    vkr_rows = []
    for i, s in enumerate(students, 1):
        vkr_rows.append(f"  [{i}], [{c.escape_typst(c.g(s, 'ФИО'))}], [{_topic_full(s)}], "
                        f"[{c.escape_typst(c.g(s, 'руководитель'))}],")
    vkr_tbl = ("#table(\n    columns: (0.25fr, 1fr, 1fr, 1fr),\n    stroke: 0.25pt,\n"
               "    [№], [ФИО], [тема ВКР], [научный руководитель ВКР],\n"
               + "\n".join(vkr_rows) + "\n  )\n")

    join = lambda lst: ", ".join(c.escape_typst(x) for x in lst) if lst else "Отсутствуют."

    fac_e = c.escape_typst(fac)
    title = (
        LETTERHEAD
        + "#v(3em)\n#align(horizon + center)[\n"
        f"факультет: {fac_e} #v(1em)\n"
        "#upper()[*государственная итоговая аттестация*]\n#v(2em)\n"
        f"{c.escape_typst(report_date)} #h(1fr) г. Москва\n#v(3em)\n"
        "#upper()[*отчёт* #v(1em) *председателя государственной экзаменационной комиссии*]\n"
        f"\\ по государственной итоговой аттестации выпускников #v(1em) {napr_e}\n]\n"
        "#v(2em)\n#set par(justify: false)\n"
        "#table(\n    columns: (0.5fr, 1fr),\n    stroke: none,\n"
        f"    [направленность (профиль):], [{prog_e}],\n"
        f"    [форма обучения:], [{c.escape_typst(form)}],\n  )\n"
        "#set par(justify: true)\n#pagebreak()\n"
        "#upper()[*Присутствовали*]\n#v(1em)\n" + comm_tbl + "#pagebreak()\n"
    )

    body = (
        "= Дата и номер приказа о составе государственной экзаменационной комиссии\n#v(0.5em)\n"
        f"Приказ от {c.escape_typst(gek_order_date)} № {c.escape_typst(gek_order_num)} «Об утверждении "
        "состава и секретарей государственных экзаменационных комиссий на 2026 год».\n\n"

        "= Структура государственной экзаменационной комиссии\n#v(0.5em)\n" + comm_tbl + "\n"

        "= Перечень аттестационных испытаний, входящих в состав государственной итоговой аттестации\n#v(0.5em)\n"
        f"В соответствии с программой государственной итоговой аттестации по направлению подготовки "
        f"{napr_e} государственная итоговая аттестация выпускников {et} 2026 года по направлению "
        f"подготовки {napr_e}, направленность (профиль) «{prog_e}» состоит из защиты выпускной "
        "квалификационной работы. Обучающиеся были заранее ознакомлены с утверждённой программой "
        "государственной итоговой аттестации, размещённой в установленные сроки в свободном доступе.\n\n"

        "= Качественный состав государственной экзаменационной комиссии\n#v(0.5em)\n"
        f"Состав государственной экзаменационной комиссии полностью обеспечивает квалифицированное "
        f"рассмотрение выпускных квалификационных работ обучающихся по направлению подготовки {napr_e}. "
        f"За отчётный период государственная экзаменационная комиссия провела {sessions or '____'} "
        f"заседаний и аттестовала {total} обучающихся на защите выпускных квалификационных работ очной "
        f"формы обучения по направлению подготовки {napr_e}, направленность (профиль) «{prog_e}». "
        "В своей работе государственная экзаменационная комиссия руководствовалась нормативными актами "
        "Российской Федерации и локальными нормативными актами АНО ВО «Универсальный университет».\n\n"

        "= Анализ аттестационных испытаний (по видам)\n#v(0.5em)\n"
        "Выпускные квалификационные работы, представленные к защите:\n#v(0.5em)\n" + vkr_tbl
        + "#v(0.5em)\nРезультаты защиты выпускных квалификационных работ:\n#v(0.5em)\n"
        + _results_table(total, by_grade, passed, len(honors)) + "\n"

        "= ФИО обучающихся, получивших диплом о высшем образовании с отличием\n#v(0.5em)\n"
        f"{join(honors)}\n\n"

        "= ФИО обучающихся, получивших неудовлетворительные оценки\n#v(0.5em)\n"
        f"{join(unsat)}\n\n"

        "= ФИО обучающихся, рекомендованных к поступлению в магистратуру / аспирантуру\n#v(0.5em)\n"
        f"{join(excellent)}\n\n"

        "= Выводы об уровне подготовки выпускников\n#v(0.5em)\n"
        "Обучающиеся показали высокий уровень подготовленности по итогам освоения образовательной "
        "программы: продемонстрировали умение анализировать материал, аргументировать свою позицию и "
        "представлять результаты самостоятельной работы. Продемонстрирован хороший уровень владения "
        "компетенциями, на освоение которых ориентирована образовательная программа. На защите выпускных "
        "квалификационных работ обучающиеся показали способность ставить профессиональные задачи и "
        "находить обоснованные решения, владение методами поиска, анализа и систематизации информации. "
        "Выступления сопровождались презентациями, что позволило наглядно представить результаты работы. "
        "В целом результаты защиты свидетельствуют о том, что выпускники успешно освоили образовательную "
        "программу и готовы применять полученные знания в профессиональной деятельности.\n\n"

        "= Положительные стороны в подготовке выпускников\n#v(0.5em)\n"
        "Государственная экзаменационная комиссия отметила серьёзную работу, проделанную авторами "
        "выпускных квалификационных работ, и практическую значимость полученных результатов. Результаты "
        "защиты свидетельствуют о том, что обучающиеся успешно освоили компетенции, на которые "
        "ориентирована образовательная программа.\n\n"

        "= Недостатки в подготовке выпускников\n#v(0.5em)\n"
        "Существенных недостатков в подготовке выпускников государственной экзаменационной комиссией "
        "не выявлено.\n\n"

        "= Предложения по улучшению подготовки выпускников\n#v(0.5em)\n"
        "Члены государственной экзаменационной комиссии рекомендовали выпускникам уделять большее "
        "внимание оформлению работ в соответствии с установленными требованиями, а также усилению связи "
        "между теоретической и практической частями работ.\n\n"

        "= Предложения по организации заседания государственной экзаменационной комиссии\n#v(0.5em)\n"
        "Работа государственной экзаменационной комиссии была организована в соответствии с требованиями "
        "законодательства Российской Федерации; защита выпускных квалификационных работ проведена согласно "
        "расписанию проведения государственной итоговой аттестации, присутствовали научные руководители. "
        "При отсутствии научного руководителя отзыв зачитывался секретарём государственной экзаменационной "
        "комиссии. Заявлений на апелляцию со стороны обучающихся на процедуру защиты и результаты "
        "государственной итоговой аттестации не поступало.\n"
    )

    sign = (
        "#v(2em)\n#align(bottom)[\n#table(\n  columns: (0.5fr, 0.5fr, 0.5fr),\n  stroke: none,\n"
        "  [#align(bottom + right)[председатель ГЭК]],"
        "[#align(bottom)[#line(stroke: 0.03em, length: 100%)]],"
        f"[#align(right)[#align(bottom + left)[{_short_name_typ(chair)}]]],\n)]\n"
    )
    return PREAMBLE + title + body + sign


def generate(
    report_date: str = "«__» ________ 2026 года",
    gek_order_num: str = "_____________",
    gek_order_date: str = "«__» ________ 2026 года",
    form: str = FORM_DEFAULT,
    faculties=None, directions=None, programs=None,
    spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID,
) -> c.GenerationResult:
    res = c.GenerationResult()
    students = [s for s in c.fetch_sheet_rows(c.SHEET_STUDENTS, spreadsheet_id) if c.g(s, "ФИО")]
    students = c.filter_students(students, faculties, directions, programs)
    commissions = _build_commissions(c.fetch_sheet_rows(c.SHEET_GEK, spreadsheet_id))

    sessions = defaultdict(int)
    for r in c.fetch_sheet_rows(c.SHEET_SCHEDULE, spreadsheet_id):
        if c.g(r, "этап").lower().startswith("защита") and c.parse_gsheet_date(c.g(r, "дата")):
            sessions[(c.g(r, "факультет"), c.g(r, "программа"))] += 1

    groups = defaultdict(list)
    for s in students:
        groups[(c.g(s, "факультет"), c.g(s, "направление"), c.g(s, "программа"), c.g(s, "курс"))].append(s)

    for (fac, napr, prog, kurs), studs in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][2])):
        studs.sort(key=lambda s: c.g(s, "ФИО"))
        comm = commissions.get((fac, prog))
        doc = _build_report(napr, prog, fac, kurs, studs, comm, sessions.get((fac, prog), 0),
                            report_date, gek_order_num, gek_order_date, form)
        out_dir = c.sanitize_filename(napr)
        fname = c.sanitize_filename(f"Отчёт председателя ГЭК — {prog}.pdf")
        res.add(f"{out_dir}/{fname}", doc)
        res.log.append(f"✓ {napr} / {prog} — {len(studs)} чел.")

    return res

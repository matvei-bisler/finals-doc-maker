"""Протоколы заседаний ГЭК: индивидуальные (по студенту) + о присвоении квалификации (по профилю).

Сквозная нумерация по датам защиты (раньше дата → меньше номер). Если на профиль указано
несколько дней защиты — обучающиеся делятся по дням поровну (по алфавиту). При совпадении
дат (бакалавриат и магистратура одного профиля защищаются в одни и те же дни по «Графику»)
бакалавриат нумеруется раньше магистратуры. Вопросы к обучающемуся берутся из столбца
«вопросы» листа `2025/26` (значения через «;»); если ячейка пустая — используются вопросы
по умолчанию (stock_questions).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from . import common as c

FORM_DEFAULT = "очная"
VKR_TYPE_BACHELOR = "дипломная работа"
VKR_TYPE_MASTER = "магистерская диссертация"

STOCK_QUESTIONS = (
    "1. На каком исследовательском материале строится работа и как был организован "
    "процесс составления проекта?\n"
    "2. Как соотносятся теоретическая и практическая части работы?\n"
    "3. В чём значимость проекта для профессионального и социокультурного контекста?"
)

WORD_TO_GRADE = c.WORD_TO_GRADE
GRADE_WORD = c.GRADE_WORD

CHAR_BY_GRADE = {
    5: "Полные, развернутые ответы на вопросы, свидетельствующие об отличном владении теорией и практикой",
    4: "Самостоятельно и последовательно излагает материал, хорошо ориентируется в обязательной литературе",
    3: "Показывает базовые данные, материал излагает репродуктивно, допуская некоторые ошибки",
    2: "Не отвечает на поставленные вопросы или даёт фрагментарные ответы, свидетельствующие о недостаточном владении теорией и практикой",
}
READY_BY_GRADE = {
    5: "обучающийся практически и теоретически готов к решению профессиональных задач, степень освоения компетенций на высоком уровне",
    4: "обучающийся практически и теоретически готов к решению профессиональных задач, степень освоения компетенций на хорошем уровне",
    3: "обучающийся практически и теоретически готов к решению профессиональных задач, степень освоения компетенций на достаточном уровне",
    2: "обучающийся практически и теоретически не готов к решению профессиональных задач, компетенции не освоены",
}


def _char_block(grade) -> str:
    if grade in CHAR_BY_GRADE:
        return CHAR_BY_GRADE[grade]
    return (
        "- если «5» Полные, развернутые ответы на вопросы, свидетельствующие об отличном владении теорией и практикой\n"
        "- если «4» Самостоятельно и последовательно излагает материал, хорошо ориентируется в обязательной литературе\n"
        "- если «3» Показывает базовые данные, материал излагает репродуктивно, допуская некоторые ошибки"
    )


def _ready_block(grade) -> str:
    if grade in READY_BY_GRADE:
        return "- " + READY_BY_GRADE[grade]
    return (
        "- если «5» — обучающийся практически и теоретически готов к решению профессиональных задач, степень освоения компетенций на высоком уровне\n"
        "- если «4» — обучающийся практически и теоретически готов к решению профессиональных задач, степень освоения компетенций на хорошем уровне\n"
        "- если «3» — обучающийся практически и теоретически готов к решению профессиональных задач, степень освоения компетенций на достаточном уровне\n"
        "- если «2» — обучающийся практически и теоретически не готов к решению профессиональных задач, компетенции не освоены"
    )


def _decision_block(grade) -> str:
    base = "Признать, что государственное аттестационное испытание в форме защиты выпускной квалификационной работы"
    if grade == 2:
        return base + " не пройдено (оценка неудовлетворительно)"
    if grade in GRADE_WORD:
        return base + f" пройдено с оценкой {GRADE_WORD[grade]}"
    return base + " пройдено с оценкой \\_\\_\\_\\_\\_\\_\\_"


def _build_defense_dates(schedule_rows: list[dict]) -> dict:
    raw = defaultdict(list)
    for r in schedule_rows:
        stage = c.g(r, "этап").lower()
        if not stage.startswith("защита"):
            continue
        dt = c.parse_gsheet_date(c.g(r, "дата"))
        if dt:
            raw[(c.g(r, "факультет"), c.g(r, "программа"))].append(dt)
    return {key: sorted(set(lst)) for key, lst in raw.items()}


def _assign_dates(n_students: int, date_list: list) -> list:
    if not date_list:
        return [None] * n_students
    d = len(date_list)
    base, rem = divmod(n_students, d)
    result = []
    for i, dt in enumerate(date_list):
        size = base + (1 if i < rem else 0)
        result.extend([dt] * size)
    return result


def _date_str(dt, default_defense_date: str) -> str:
    return c.format_date_ru(dt) if dt else default_defense_date


def _build_commissions(gek_rows: list[dict]) -> dict:
    by_key = defaultdict(lambda: {"chair": None, "secretary": None, "members": []})
    for r in gek_rows:
        name = c.g(r, "ФИО")
        if not name:
            continue
        key = (c.g(r, "факультет"), c.g(r, "программа"))
        person = {"name": name, "aff": c.g(r, "аффилиация")}
        if c.truthy(r.get("председатель")):
            by_key[key]["chair"] = person
        elif c.truthy(r.get("секретарь")):
            by_key[key]["secretary"] = person
        else:
            by_key[key]["members"].append(person)
    return by_key


def _person_cell(person) -> str:
    if not person:
        return ""
    name = c.escape_typst(person["name"])
    aff = c.escape_typst(person["aff"])
    return name + (f" \\ {aff}" if aff else "")


def _build_attendees(comm) -> str:
    chair = comm["chair"] if comm else None
    secretary = comm["secretary"] if comm else None
    members = comm["members"] if comm else []

    rows = [f"    [председатель ГЭК], [{_person_cell(chair)}],"]
    if members:
        rows.append(f"    [члены ГЭК], [{_person_cell(members[0])}],")
        for m in members[1:]:
            rows.append(f"    [], [{_person_cell(m)}],")
    else:
        rows.append("    [члены ГЭК], [],")
    rows.append(f"    [секретарь ГЭК], [{_person_cell(secretary)}],")
    rows_str = "\n".join(rows)

    return (
        "*Присутствовали*:\n#v(1em)\n"
        "#table(\n    columns: (0.5fr, 1fr),\n    stroke: none,\n"
        f"{rows_str}\n  )\n"
    )


def _short_name_typ(person) -> str:
    if not person or not person.get("name"):
        return ""
    return f'#short-name("{c.escape_typst(person["name"])}")'


def _build_signatures(comm) -> str:
    chair = comm["chair"] if comm else None
    secretary = comm["secretary"] if comm else None
    return (
        "#align(bottom)[\n#table(\n  columns: (0.5fr, 0.5fr, 0.5fr),\n  stroke: none,\n"
        "  [#align(bottom + right)[председатель ГЭК]],"
        "[#align(bottom)[#line(stroke: 0.03em, length: 100%)]],"
        f"[#align(right)[#align(bottom + left)[{_short_name_typ(chair)}]]],\n"
        "  [#v(2em)#align(bottom + right)[секретарь ГЭК]],"
        "[#align(bottom)[#line(stroke: 0.03em, length: 100%)]],"
        f"[#align(right)[#align(bottom + left)[{_short_name_typ(secretary)}]]]\n)]\n"
    )


PREAMBLE = r'''#set page(paper: "a4")
#set text(size: 11pt, lang: "ru", font: "Times New Roman")
#set par(justify: true, spacing: 0.25em)
#set block(spacing: 0.25em)
#show heading.where(level: 1): set text(size: 11pt, weight: "bold")
#show heading.where(level: 1): set align(center)

#let logo = image("/pics/logo.svg")
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


def _info_table(fac: str, napr: str, prog: str, form: str) -> str:
    return (
        "#table(\n    columns: (0.5fr, 1fr),\n    stroke: none,\n"
        f"    [факультет:], [{c.escape_typst(fac)}],\n"
        f"    [направление подготовки:], [{c.escape_typst(napr)}],\n"
        f"    [профиль], [{c.escape_typst(prog)}],\n"
        f"    [форма обучения], [{c.escape_typst(form)}],\n  )\n"
    )


def _topic_ru_en(student: dict) -> str:
    topic = c.escape_typst(c.g(student, "тема"))
    title = c.g(student, "title")
    return topic + (" / " + c.escape_typst(title) if title else "")


def _is_master(year: int) -> bool:
    return year == 2


def _edu_type(year: int) -> str:
    return "магистратуры" if _is_master(year) else "бакалавриата"


def _qualification(year: int) -> str:
    return "магистр" if _is_master(year) else "бакалавр"


def _vkr_type_default(year: int, bachelor_label: str, master_label: str) -> str:
    return master_label if _is_master(year) else bachelor_label


def _diploma_label(year: int, honors: bool) -> str:
    base = "диплом магистра" if _is_master(year) else "диплом бакалавра"
    return base + " с отличием" if honors else base


def _student_questions(student: dict, default_questions: str) -> str:
    """Вопросы по студенту из столбца «вопросы» (разделены «;»); если пусто — вопросы по умолчанию."""
    parts = [p.strip() for p in c.g(student, "вопросы").split(";")]
    parts = [p for p in parts if p]
    if not parts:
        return default_questions
    return "\n".join(f"{i}. {c.escape_typst(p)}" for i, p in enumerate(parts, start=1))


def _build_individual(num, defense_date, fac, napr, prog, form, vkr_type, student, comm,
                      stock_questions: str) -> str:
    name = c.escape_typst(c.g(student, "ФИО"))
    supervisor = c.escape_typst(c.g(student, "руководитель"))
    grade = c.parse_grade(c.g(student, "оценка"))
    stock_questions = _student_questions(student, stock_questions)

    head = (
        "#align(center)[\n#v(1em)\n"
        f"#upper()[Протокол №{num}]\n"
        "\\ заседания государственной экзаменационной комиссии \\\n"
        f"от {c.escape_typst(defense_date)} \\\n"
        "по проведению государственного аттестационного испытания \\\n"
        "в форме защиты выпускной квалификационной работы\n]\n#v(1em)\n"
    )

    student_table = (
        "#v(1em)\n#table(\n    columns: (0.5fr, 1fr),\n    stroke: none,\n"
        f"    [обучающийся (ФИО):], [{name}],\n"
        f"    [вид ВКР], [{c.escape_typst(vkr_type)}],\n"
        f"    [тема ВКР], [{_topic_ru_en(student)}],\n"
        f"    [ВКР выполнена под руководством], [{supervisor}],\n  )\n"
    )

    body = (
        "#v(1em)\n"
        "В государственную экзаменационную комиссию представлены следующие материалы:\n"
        "#v(1em)\n"
        "1. Текст ВКР.\n"
        "2. Отзыв руководителя ВКР и рецензента (при наличии).\n"
        "3. Справка о результатах проверки текста ВКР на объём заимствований.\n"
        "#v(1em)\n"
        f"Перечень заданных обучающемуся вопросов:\n{stock_questions}\n\n"
        "Характеристика ответов на них:\n#v(1em)\n"
        f"{_char_block(grade)}\n#v(1em)\n"
        "Мнения председателя и членов ГЭК о выявленном в ходе государственного аттестационного "
        "испытания уровне подготовленности обучающегося к решению профессиональных задач, а также "
        "о выявленных недостатках в теоретической и практической подготовке обучающегося:\n#v(1em)\n"
        f"{_ready_block(grade)}\n#v(1em)\n"
        "Решение ГЭК:\n"
        f"{_decision_block(grade)}\n#v(1em)\n"
    )

    return (head + _info_table(fac, napr, prog, form) + "#v(1em)\n" + _build_attendees(comm)
            + student_table + body + _build_signatures(comm))


def _build_total(num, defense_date, fac, napr, prog, form, year, students, comm) -> str:
    edu_type = _edu_type(year)
    qual = _qualification(year)

    rows = []
    for s in students:
        honors = c.truthy(s.get("диплом с отличием"))
        rows.append(f"   [{c.escape_typst(c.g(s, 'ФИО'))}], [{_diploma_label(year, honors)}],")
    rows_str = "\n".join(rows)

    head = (
        "#align(center)[\n#v(1em)\n"
        f"#upper()[Протокол №{num}]\n"
        "\\ заседания государственной экзаменационной комиссии \\\n"
        f"от {c.escape_typst(defense_date)} \\\n"
        "о присвоении квалификации и выдаче документов \\ о высшем образовании и о квалификации\n]\n#v(1em)\n"
    )

    body = (
        "#v(1em)\n*В государственную экзаменационную комиссию представлены следующие материалы:*\n"
        "#v(1em)\n"
        "1. Протоколы заседаний государственной экзаменационной комиссии по проведению "
        "государственного аттестационного испытания в форме защиты выпускной квалификационной работы.\n"
        "2. Учебные карточки обучающихся.\n#v(1em)\n"
        "*Слушали* \\\n"
        f"Председателя ГЭК о результатах государственной итоговой аттестации обучающихся "
        f"образовательной программы {edu_type} {c.escape_typst(napr)}, направленность (профиль) {c.escape_typst(prog)}\n\n"
        "*Постановили:*\n"
        f"1. Присвоить квалификацию {qual} по направлению подготовки {c.escape_typst(napr)}\n"
        "2. Выдать документ о высшем образовании и о квалификации нижеперечисленным обучающимся:\n"
        "#v(1em)\n#table(\n    columns: (1fr, 0.5fr),\n    stroke: 0.25pt,\n"
        f"{rows_str}\n  )\n"
    )

    return head + _info_table(fac, napr, prog, form) + "#v(1em)\n" + _build_attendees(comm) + body + _build_signatures(comm)


def generate(
    form: str = FORM_DEFAULT,
    vkr_type_bachelor: str = VKR_TYPE_BACHELOR,
    vkr_type_master: str = VKR_TYPE_MASTER,
    stock_questions: str = STOCK_QUESTIONS,
    default_defense_date: str = "«__» ________ 2026 года",
    faculties=None, directions=None, programs=None,
    spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID,
) -> c.GenerationResult:
    res = c.GenerationResult()

    # Нумерация должна быть глобальной по всему графику защит, даже если генерируется только
    # часть программ — поэтому группы строятся по ВСЕМ обучающимся, а фильтр применяется только
    # к тому, какие профили попадут в результат (см. ниже, после расчёта номеров).
    students_rows = c.fetch_sheet_rows(c.SHEET_STUDENTS, spreadsheet_id)
    gek_rows = c.fetch_sheet_rows(c.SHEET_GEK, spreadsheet_id)
    schedule_rows = c.fetch_sheet_rows(c.SHEET_SCHEDULE, spreadsheet_id)

    commissions = _build_commissions(gek_rows)
    defense_dates = _build_defense_dates(schedule_rows)

    groups = defaultdict(list)
    for row in students_rows:
        if not c.g(row, "ФИО"):
            continue
        key = (c.g(row, "факультет"), c.g(row, "направление"), c.g(row, "программа"), c.g(row, "курс"))
        groups[key].append(row)

    infos = []
    for (fac, napr, prog, year_s), students in groups.items():
        students.sort(key=lambda s: c.g(s, "ФИО"))
        dts = defense_dates.get((fac, prog), [])
        infos.append({
            "fac": fac, "napr": napr, "prog": prog, "year": c.parse_year(year_s), "year_s": year_s,
            "students": students, "dates": dts,
            "student_dates": _assign_dates(len(students), dts),
            "earliest": dts[0] if dts else None,
        })

    # При совпадении дат защиты (в «Графике» они не различаются по курсу, поэтому у бакалавриата
    # и магистратуры одного профиля даты совпадают) бакалавриат идёт раньше магистратуры.
    infos.sort(key=lambda it: (
        it["earliest"] is None, it["earliest"] or datetime.max,
        it["napr"], it["prog"], _is_master(it["year"]), it["year"],
    ))

    num = 1
    res.log.append(f"Профилей (всего по графику): {len(infos)}")
    for it in infos:
        fac, napr, prog, year = it["fac"], it["napr"], it["prog"], it["year"]
        include = c.matches_filter(it["students"][0], faculties, directions, programs)

        comm = commissions.get((fac, prog))
        vkr_type = _vkr_type_default(year, vkr_type_bachelor, vkr_type_master)
        profile_dir = f"{c.sanitize_filename(napr)}/{c.sanitize_filename(prog)}"

        start = num
        for student, dt in zip(it["students"], it["student_dates"]):
            if include:
                doc = (PREAMBLE + LETTERHEAD
                       + _build_individual(num, _date_str(dt, default_defense_date), fac, napr, prog,
                                           form, vkr_type, student, comm, stock_questions))
                fname = c.sanitize_filename(f"Протокол №{num} {c.g(student, 'ФИО')}.pdf")
                res.add(f"{profile_dir}/{fname}", doc)
            num += 1

        total_num = num
        if include:
            total_date = _date_str(it["dates"][-1] if it["dates"] else None, default_defense_date)
            total_doc = (PREAMBLE + LETTERHEAD
                         + _build_total(total_num, total_date, fac, napr, prog, form, year, it["students"], comm))
            res.add(f"{profile_dir}/{c.sanitize_filename(f'Протокол №{total_num} о присвоении квалификации.pdf')}", total_doc)
        num += 1

        if include:
            days = ", ".join(c.format_date_ru(d) for d in it["dates"]) or "—"
            res.log.append(f"• {napr} / {prog} ({it['year_s']} курс) — {len(it['students'])} чел.; "
                            f"протоколы №{start}–{total_num}; дни защиты: {days}"
                            + ("" if comm else "  [комиссия не задана]"))

    res.log.append(f"Всего протоколов по графику: {num - 1}; сгенерировано в этой выборке: {len(res.files)}")
    return res

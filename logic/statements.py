"""Заявления студентов на имя М.В. Марковой (руководитель Департамента академического качества).

Три типа, один общий шаблон (адаптирован из generate_separate.ipynb — заявление на утверждение
темы ВКР): letterhead + шапка «от ФИО, студента N курса…» + текст заявления + подпись + контакты.

  1) topics   — утверждение темы ВКР (оригинальный шаблон)
  2) gia_ack  — ознакомление с требованиями и особенностями организации и проведения ГИА
  3) vacation — последипломные каникулы

Один PDF на каждого обучающегося, разложены по факультет/направление/программа.
"""
from __future__ import annotations

from . import common as c

PREAMBLE = r'''#let short-name(name) = {
  let p = name.split(" ").filter(x => x != "")
  if p.len() >= 3 { [#p.at(0) #p.at(1).first(). #p.at(2).first().] }
  else if p.len() == 2 { [#p.at(0) #p.at(1).first().] }
  else { [#name] }
}

#let logo = image("/pics/logo.svg")

#set page(paper: "a4")
#set text(size: 11pt, lang: "ru", font: "Times New Roman")
#set par(justify: true, spacing: 0.25em)
#set block(spacing: 0.25em)
#show heading.where(level: 1): set text(size: 14pt, weight: "bold")
#show heading.where(level: 1): set align(center)
'''

LETTERHEAD = r'''#set text(size: 10pt, lang: "ru", font: "Times New Roman")
#set par(justify: false)
#table(
  columns: (1fr, 3fr),
  stroke: (left: 0pt, right: 0pt, top: 0pt, bottom: 0pt),
  column-gutter: 0.5em,
  table.vline(x: 1, stroke: 0.5pt),
  [#align(horizon)[#logo]],
  [
    #v(0.75em)
    #text(font: "Times New Roman", size: 9pt)[#align(horizon)[
      АНО ВО «Универсальный Университет» \ ОГРН 1197700010518 \ 105120, Россия, г. Москва, Центр дизайна ARTPLAY \ ул. Нижняя Сыромятническая, д. 10, стр. 3]
    ]
  ],
)
#set text(size: 11pt, lang: "ru", font: "Times New Roman")
#set par(justify: true, spacing: 0.25em)
'''


def _addressee_block(student: dict) -> str:
    fio = c.escape_typst(c.g(student, "ФИО"))
    year = c.escape_typst(c.g(student, "курс"))
    direction = c.escape_typst(c.g(student, "направление"))
    program = c.escape_typst(c.g(student, "программа"))
    return (
        "#v(3em)\n"
        "#align(right)[\n"
        "  Руководителю \\ Департамента академического качества \\ АНО ВО «Универсальный Университет» \\\n"
        "  Марковой Марии Владимировне\n"
        "  #v(1em)\n"
        f"  от {fio} \\ студента/ки {year} курса \\ направления подготовки {direction} \\ "
        f"профиля \"{program}\"\n"
        "]\n"
    )


def _signature_block(student: dict, date_str: str) -> str:
    fio = c.escape_typst(c.g(student, "ФИО"))
    return (
        "#set align(bottom + left)\n"
        "#v(2em)\n"
        "#table(\n"
        "  columns: (2fr, 2fr, 2fr),\n"
        "  stroke: none,\n"
        f"  [{c.escape_typst(date_str)} \\\n],"
        "[#align(bottom)[#line(stroke: 0.03em, length: 100%)]],"
        f"[#align(right)[#align(bottom)[\\/ #short-name(\"{fio}\")]]]\n"
        ")\n"
        "#v(5em)\n"
        "#table(\n"
        "  columns: (2.6fr, 1fr),\n"
        "  stroke: (left: 0pt, right: 0pt, top: 0pt, bottom: 0pt),\n"
        "  align: horizon + left,\n"
        "  column-gutter: 0.5em,\n"
        "  [],\n"
        "  [\n"
        "    #v(0.75em)\n"
        '    #text(font: "Times New Roman", 9pt)[#align[\n'
        "      | info\\@u.university \\ | www.u.university \\ | Тел./факс: +7 (495) 640-30-92]\n"
        "    ]\n"
        "  ],\n"
        ")\n"
    )


def _doc(student: dict, body: str, date_str: str) -> str:
    return (
        PREAMBLE + LETTERHEAD
        + _addressee_block(student)
        + "\n#v(2em)\n= " + '#upper("Заявление")\n#v(2em)\n'
        + body
        + _signature_block(student, date_str)
    )


# ---- 1) Утверждение темы ВКР ----
def _body_topics(student: dict) -> str:
    topic = c.escape_typst(c.g(student, "тема"))
    title = c.g(student, "title")
    full_topic = topic + " / " + c.escape_typst(title) if title else topic
    return f"Прошу утвердить тему моей выпускной квалификационной работы: {full_topic}.\n"


# ---- 2) Ознакомление с требованиями и особенностями организации и проведения ГИА ----
def _body_gia_ack(student: dict) -> str:
    direction = c.escape_typst(c.g(student, "направление"))
    program = c.escape_typst(c.g(student, "программа"))
    return (
        f"Настоящим подтверждаю, что ознакомлен(а) с требованиями и особенностями организации "
        f"и проведения государственной итоговой аттестации по направлению подготовки {direction}, "
        f"направленность (профиль) «{program}», в том числе с Программой государственной итоговой "
        "аттестации, расписанием, формой и порядком проведения государственного аттестационного "
        "испытания в форме защиты выпускной квалификационной работы, а также с критериями "
        "оценивания результатов государственной итоговой аттестации.\n\n"
        "Претензий и возражений по порядку организации и проведения государственной итоговой "
        "аттестации не имею.\n"
    )


# ---- 3) Последипломные каникулы ----
def _body_vacation(student: dict, start_date: str, end_date: str) -> str:
    direction = c.escape_typst(c.g(student, "направление"))
    program = c.escape_typst(c.g(student, "программа"))
    return (
        f"Прошу предоставить мне последипломные каникулы после прохождения государственной "
        f"итоговой аттестации по направлению подготовки {direction}, направленность (профиль) "
        f"«{program}», с {c.escape_typst(start_date)} по {c.escape_typst(end_date)}.\n"
    )


def _generate_common(body_fn, out_prefix: str, date_str: str,
                     faculties=None, directions=None, programs=None,
                     spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID) -> c.GenerationResult:
    res = c.GenerationResult()
    rows = c.fetch_sheet_rows(c.SHEET_STUDENTS, spreadsheet_id)
    rows = [r for r in rows if c.g(r, "ФИО")]
    rows = c.filter_students(rows, faculties, directions, programs)
    res.log.append(f"✓ Обучающихся после фильтра: {len(rows)}")

    for s in rows:
        fio = c.g(s, "ФИО")
        napr, prog = c.g(s, "направление"), c.g(s, "программа")
        doc = _doc(s, body_fn(s), date_str)
        relpath = (f"{c.sanitize_filename(napr)}/{c.sanitize_filename(prog)}/"
                   f"{c.sanitize_filename(f'{out_prefix} — {fio}.pdf')}")
        res.add(relpath, doc)

    res.log.append(f"✓ Готово: {len(res.files)} заявлений.")
    return res


def generate_topics(date_str: str = "«__» ________ 2026 года", faculties=None, directions=None,
                    programs=None, spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID) -> c.GenerationResult:
    return _generate_common(_body_topics, "Заявление об утверждении темы ВКР", date_str,
                            faculties, directions, programs, spreadsheet_id)


def generate_gia_ack(date_str: str = "«__» ________ 2026 года", faculties=None, directions=None,
                     programs=None, spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID) -> c.GenerationResult:
    return _generate_common(_body_gia_ack, "Заявление об ознакомлении с ГИА", date_str,
                            faculties, directions, programs, spreadsheet_id)


def generate_vacation(date_str: str = "«__» ________ 2026 года",
                      start_date: str = "«__» ________ 2026 года",
                      end_date: str = "«__» ________ 2026 года",
                      faculties=None, directions=None, programs=None,
                      spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID) -> c.GenerationResult:
    return _generate_common(lambda s: _body_vacation(s, start_date, end_date),
                            "Заявление на последипломные каникулы", date_str,
                            faculties, directions, programs, spreadsheet_id)

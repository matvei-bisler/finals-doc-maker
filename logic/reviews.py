"""Отзывы научных руководителей и рецензии на ВКР — по одному PDF на каждого обучающегося.

Оценка/текст подтягиваются из отдельных Google-таблиц (создаёт Apps Script
generate_review_tables.gs), по «Реестру файлов» в мастер-таблице. Если реестра/данных
нет — генерируются заготовки с прочерками под ручное заполнение.
"""
from __future__ import annotations

import re

from . import common as c


def _par_typst(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "\n\n".join(" \\\n".join(c.escape_typst(line) for line in p.splitlines()) for p in paras)


def _blank(n: int) -> str:
    return "\\_" * n


def load_review_data(spreadsheet_id: str) -> tuple[dict, dict, list[str]]:
    """Возвращает (отзывы, рецензии, лог): ФИО -> {'оценка':..., 'текст':...}."""
    otzyv, rec, log = {}, {}, []
    try:
        reg = c.matrix_to_dicts(c.fetch_csv_matrix(spreadsheet_id, c.SHEET_REGISTRY))
    except Exception as e:
        log.append(f"⚠ Реестр «{c.SHEET_REGISTRY}» не прочитан ({e}); тексты/оценки будут пустыми.")
        return otzyv, rec, log

    by_type = {"отзыв": otzyv, "рецензия": rec}
    for r in reg:
        target = by_type.get(c.g(r, "тип"))
        fid = c.g(r, "id")
        if target is None or not fid:
            continue
        try:
            matrix = c.fetch_csv_matrix(fid)
        except Exception as e:
            log.append(f"  ⚠ не прочитан файл {c.g(r, 'имя файла')} ({fid}): {e}")
            continue
        hi = next((i for i, row in enumerate(matrix) if row and row[0].strip().lower() == "фио"), None)
        if hi is None:
            continue
        hdr = [cell.strip().lower() for cell in matrix[hi]]
        j_grade = hdr.index("оценка") if "оценка" in hdr else None
        j_text = next((j for j, cell in enumerate(hdr) if cell.startswith("текст")), None)
        for row in matrix[hi + 1:]:
            if not row or not row[0].strip():
                continue
            cell = lambda j: row[j].strip() if (j is not None and j < len(row)) else ""
            target[row[0].strip()] = {"оценка": cell(j_grade), "текст": cell(j_text)}

    log.append(f"✓ Реестр: отзывов с данными {len(otzyv)}, рецензий с данными {len(rec)}")
    return otzyv, rec, log


PREAMBLE = r'''#let logo = image("/pics/logo.svg")
#set page(paper: "a4")
#set text(size: 11pt, lang: "ru", font: "Times New Roman")
#set par(justify: true, spacing: 0.25em)
#set block(spacing: 0.25em)

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


def _topic_ru_en(student: dict) -> str:
    topic = c.escape_typst(c.g(student, "тема"))
    title = c.g(student, "title")
    return topic + (" / " + c.escape_typst(title) if title else "")


def _info_table(student: dict) -> str:
    return (
        "#table(\n    columns: (0.5fr, 1fr),\n    stroke: none,\n"
        f"    [обучающийся (ФИО):], [{c.escape_typst(c.g(student, 'ФИО'))}],\n"
        f"    [направление подготовки:], [{c.escape_typst(c.g(student, 'направление'))}],\n"
        f"    [направленность (профиль):], [{c.escape_typst(c.g(student, 'программа'))}],\n"
        f"    [тема ВКР:], [{_topic_ru_en(student)}],\n  )\n"
    )


def _signature(role: str, person_full: str, short: bool) -> str:
    name = (f'#short-name("{c.escape_typst(person_full)}")' if short and person_full
            else c.escape_typst(person_full))
    return (
        "#v(3em)\n#table(\n  columns: (0.5fr, 0.5fr, 0.5fr),\n  stroke: none,\n"
        f"  [#align(bottom + right)[{c.escape_typst(role)}]],"
        "[#align(bottom)[#line(stroke: 0.03em, length: 100%)]],"
        f"[#align(right)[#align(bottom + left)[{name}]]],\n)\n"
    )


def _build_otzyv(student: dict, supervisor: str, data: dict | None) -> str:
    grade = c.escape_typst((data or {}).get("оценка", "")) or _blank(14)
    text = _par_typst((data or {}).get("текст", "")) or \
        "#text(fill: gray)[_(текст отзыва — заполняется научным руководителем)_]"
    sup_name = supervisor.split(",")[0].strip()

    return (
        LETTERHEAD + "#v(1em)\n"
        + "#align(center)[#upper()[*Отзыв*] \\\nнаучного руководителя о выпускной квалификационной работе]\n"
        + "#v(1em)\n" + _info_table(student) + "#v(1em)\n"
        + f"Научный руководитель: {c.escape_typst(supervisor)}\n#v(1em)\n"
        + text + "\n#v(1em)\n"
        + f"Рекомендуемая оценка: {grade}\n"
        + _signature("научный руководитель", sup_name, short=True)
    )


def _build_rec(student: dict, reviewers: str, data: dict | None) -> str:
    grade = c.escape_typst((data or {}).get("оценка", "")) or _blank(14)
    text = _par_typst((data or {}).get("текст", "")) or \
        "#text(fill: gray)[_(текст рецензии — заполняется рецензентом)_]"

    return (
        LETTERHEAD + "#v(1em)\n"
        + "#align(center)[#upper()[*Рецензия*] \\\nна выпускную квалификационную работу]\n"
        + "#v(1em)\n" + _info_table(student) + "#v(1em)\n"
        + f"Рецензент: {c.escape_typst(reviewers)}\n#v(1em)\n"
        + text + "\n#v(1em)\n"
        + f"Рекомендуемая оценка: {grade}\n"
        + _signature("рецензент", reviewers, short=False)
    )


def generate(faculties=None, directions=None, programs=None,
            spreadsheet_id: str = c.DEFAULT_SPREADSHEET_ID) -> c.GenerationResult:
    res = c.GenerationResult()
    students = c.matrix_to_dicts(c.fetch_csv_matrix(spreadsheet_id, c.SHEET_STUDENTS))
    students = [s for s in students if c.g(s, "ФИО")]
    students = c.filter_students(students, faculties, directions, programs)
    res.log.append(f"✓ Обучающихся после фильтра: {len(students)}")

    otzyv_data, rec_data, load_log = load_review_data(spreadsheet_id)
    res.log.extend(load_log)

    n_otz = n_rec = 0
    for s in students:
        fio = c.g(s, "ФИО")
        napr, prog = c.g(s, "направление"), c.g(s, "программа")
        profile_dir = f"{c.sanitize_filename(napr)}/{c.sanitize_filename(prog)}"

        supervisor = c.g(s, "руководитель")
        if supervisor:
            doc = PREAMBLE + _build_otzyv(s, supervisor, otzyv_data.get(fio))
            res.add(f"{profile_dir}/{c.sanitize_filename(f'Отзыв — {fio}.pdf')}", doc)
            n_otz += 1

        reviewers = c.g(s, "рецензент")
        if reviewers:
            doc = PREAMBLE + _build_rec(s, reviewers, rec_data.get(fio))
            res.add(f"{profile_dir}/{c.sanitize_filename(f'Рецензия — {fio}.pdf')}", doc)
            n_rec += 1

    res.log.append(f"✓ Готово. Отзывов: {n_otz}, рецензий: {n_rec}.")
    return res

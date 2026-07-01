"""Приказ об утверждении состава апелляционной комиссии — один файл на все направления."""
from __future__ import annotations

from . import common as c

SUBTITLE = "Об утверждении состава апелляционной \\ комиссии на 2026 год"

DEFAULT_MEMBERS = [
    {"role": "Председатель", "text": "Саввин Афанасий Афанасьевич, директор АНО ВО «Универсальный университет»"},
    {"role": "Заместитель председателя", "text": "Маркова Мария Владимировна, руководитель группы дизайнеров образовательных программ высшего образования"},
    {"role": "Член комиссии", "text": "Буракова Алла Дмитриевна, руководитель учебного отдела программ высшего образования"},
    {"role": "Член комиссии", "text": "Кузьмина Дарья Алексеевна, руководитель направления академического развития и контроля"},
]


def _body(members: list[dict]) -> str:
    lines = []
    role_seen_member = False
    for m in members:
        role, text = m["role"].strip(), m["text"].strip()
        if not text:
            continue
        if role.lower().startswith("член"):
            if not role_seen_member:
                lines.append("Члены комиссии:")
                role_seen_member = True
            lines.append(c.escape_typst(text))
        else:
            lines.append(f"{c.escape_typst(role)}: {c.escape_typst(text)}")
    body_text = " \\\n".join(lines)
    return (
        "Утвердить состав апелляционной комиссии на 2026 год по образовательным программам "
        "высшего образования:\n"
        "#v(0.3em)\n#block[\n" + body_text + "\n]\n"
    )


def generate(order_date: str, order_num_start: int = 1,
             members: list[dict] | None = None) -> c.GenerationResult:
    res = c.GenerationResult()
    members = members if members is not None else DEFAULT_MEMBERS
    onum = c.order_num_from_date(order_date, order_num_start)
    doc = c.build_prikaz_header(onum, order_date, SUBTITLE) + _body(members) + c.build_prikaz_footer()
    res.add("Приказ об апелляционной комиссии.pdf", doc)
    res.log.append(f"  № {onum}: апелляционная комиссия (один файл на все направления)")
    return res

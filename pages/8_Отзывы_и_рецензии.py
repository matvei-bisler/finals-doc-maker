from pathlib import Path

import streamlit as st

from logic import common as c
from logic import reviews
from ui_helpers import download_results, scope_widgets, sidebar_data_source

st.set_page_config(page_title="Отзывы и рецензии", page_icon="✍️", layout="wide")
sid = sidebar_data_source()

st.title("✍️ Отзывы научных руководителей и рецензии на ВКР")
st.caption(
    "PDF на каждого обучающегося: отзыв — всегда (руководитель есть у всех), рецензия — "
    "только если в «2025/26» указан рецензент."
)

st.markdown("""
Тексты отзывов/рецензий заполняются **не здесь**, а в отдельных Google-таблицах — по одной на
программу (отзывы) и по одной на рецензента (рецензии). Их создаёт Apps Script, встроенный в
саму таблицу «ВКР UU»:

1. Открой таблицу → меню **«ВКР» → «Создать / обновить таблицы отзывов и рецензий»**.
2. Скрипт создаст (или обновит) таблицы в папке Google Диска рядом с исходным файлом и запишет
   их id во вкладку **«Реестр файлов»** мастер-таблицы.
3. Разошли ссылки на нужные таблицы руководителям/рецензентам — редактировать там можно только
   столбцы «оценка» и «текст», остальное защищено.
4. Когда данные заполнены — жми «Сгенерировать» ниже: соберутся финальные PDF по каждому студенту.
""")

_gs_path = Path(__file__).resolve().parents[2] / "finals" / "archive" / "generate_review_tables.gs"
with st.expander("📜 Код Apps Script (generate_review_tables.gs)"):
    if _gs_path.exists():
        st.code(_gs_path.read_text(encoding="utf-8"), language="javascript")
    else:
        st.warning(f"Файл не найден: {_gs_path}")

st.divider()

faculties, directions, programs = scope_widgets(sid, key_prefix="reviews")

if st.button("🚀 Сгенерировать PDF отзывов и рецензий", type="primary"):
    with st.spinner("Читаю реестр, тяну оценки/тексты, собираю PDF…"):
        res = reviews.generate(faculties=faculties, directions=directions, programs=programs,
                               spreadsheet_id=sid)
    download_results(res, key_prefix="reviews", zip_name="Отзывы и рецензии")

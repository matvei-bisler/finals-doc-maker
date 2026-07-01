import pandas as pd
import streamlit as st

from logic import common as c
from logic import dopusk_gia
from ui_helpers import download_results, scope_widgets, sidebar_data_source

st.set_page_config(page_title="Приказ: допуск к ГИА", page_icon="✅", layout="wide")
sid = sidebar_data_source()

st.title("✅ Приказ(-ы) о допуске к прохождению ГИА")
st.caption(
    "Группирует обучающихся по направлению/профилю, определяет период ГИА по правилам ниже, "
    "дата приказа — N рабочих дней до начала ГИА. Приказы за один день объединяются в один файл "
    "с нумерацией 1, 2, 3… внутри дня."
)

st.info(
    "⚠️ В исходном ноутбуке жёстко брались только студенты **4 курса** — это молча исключало "
    "архитектуру (5 курс) и магистратуру (2 курс) из допуска. Здесь курсы выбираются явно.",
    icon="⚠️",
)

days_before = st.number_input("За сколько рабочих дней до начала ГИА издавать приказ", min_value=0, max_value=10, value=2)

with st.spinner("Загружаю список курсов из таблицы…"):
    try:
        rows = c.fetch_sheet_rows(c.SHEET_STUDENTS, sid)
        available_courses = sorted({c.g(r, "курс") for r in rows if c.g(r, "ФИО") and c.g(r, "курс")})
    except Exception as e:
        available_courses = []
        st.error(f"Не удалось прочитать таблицу: {e}")

courses = st.multiselect("Курсы, для которых издаётся приказ о допуске", options=available_courses,
                          default=available_courses)

faculties, directions, programs = scope_widgets(sid, key_prefix="dopusk")

st.subheader("Периоды ГИА по программам")
st.caption("Первое совпадение подстроки в названии программы (без учёта регистра) побеждает. "
           "Можно менять даты, добавлять/удалять строки.")

rules_df = st.data_editor(
    pd.DataFrame(dopusk_gia.DEFAULT_GIA_RULES),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "keyword": st.column_config.TextColumn("Подстрока в программе"),
        "start": st.column_config.TextColumn("Начало ГИА (ДД.ММ.ГГГГ)"),
        "end": st.column_config.TextColumn("Конец ГИА (ДД.ММ.ГГГГ)"),
    },
    key="gia_rules_editor",
)

col1, col2 = st.columns(2)
with col1:
    fallback_start = st.text_input("Период по умолчанию — начало", value=dopusk_gia.DEFAULT_FALLBACK["start"])
with col2:
    fallback_end = st.text_input("Период по умолчанию — конец", value=dopusk_gia.DEFAULT_FALLBACK["end"])

if st.button("🚀 Сгенерировать", type="primary"):
    rules = rules_df.to_dict("records")
    fallback = {"start": fallback_start, "end": fallback_end}
    with st.spinner("Читаю таблицу и собираю приказы…"):
        res = dopusk_gia.generate(
            days_before=int(days_before), courses=courses, rules=rules, fallback=fallback,
            faculties=faculties, directions=directions, programs=programs,
            spreadsheet_id=sid,
        )
    download_results(res, key_prefix="dopusk_gia")

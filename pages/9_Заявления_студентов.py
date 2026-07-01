from datetime import date

import streamlit as st

from logic import common as c
from logic import statements
from ui_helpers import download_results, require_password, scope_widgets, sidebar_data_source

st.set_page_config(page_title="Заявления студентов", page_icon="🖊️", layout="wide")
require_password()
sid = sidebar_data_source()

st.title("🖊️ Заявления студентов")
st.caption(
    "Один PDF на каждого обучающегося. Шаблон адаптирован из «заявления об утверждении темы "
    "ВКР» — letterhead, шапка на имя М.В. Марковой (руководитель Департамента академического "
    "качества), подпись и контакты одинаковые для всех трёх типов."
)

tab1, tab2, tab3 = st.tabs([
    "📝 Утверждение темы ВКР", "✅ Ознакомление с ГИА", "🏖️ Последипломные каникулы",
])

with tab1:
    st.markdown("Прошу утвердить тему выпускной квалификационной работы (тема — из «2025/26», рус./англ. через «/»).")
    faculties1, directions1, programs1 = scope_widgets(sid, key_prefix="stmt_topics")
    date1 = st.date_input("Дата заявления", value=date(2026, 3, 15), key="stmt_topics_date")
    if st.button("🚀 Сгенерировать", type="primary", key="stmt_topics_btn"):
        with st.spinner("Собираю заявления…"):
            res = statements.generate_topics(
                date_str=c.date_to_order_string(date1),
                faculties=faculties1, directions=directions1, programs=programs1, spreadsheet_id=sid,
            )
        download_results(res, key_prefix="stmt_topics", zip_name="Заявления — тема ВКР")

with tab2:
    st.markdown(
        "Подтверждение, что обучающийся ознакомлен с требованиями и особенностями организации "
        "и проведения ГИА по своему направлению/профилю."
    )
    faculties2, directions2, programs2 = scope_widgets(sid, key_prefix="stmt_gia")
    date2 = st.date_input("Дата заявления", value=date(2026, 3, 15), key="stmt_gia_date")
    if st.button("🚀 Сгенерировать", type="primary", key="stmt_gia_btn"):
        with st.spinner("Собираю заявления…"):
            res = statements.generate_gia_ack(
                date_str=c.date_to_order_string(date2),
                faculties=faculties2, directions=directions2, programs=programs2, spreadsheet_id=sid,
            )
        download_results(res, key_prefix="stmt_gia", zip_name="Заявления — ознакомление с ГИА")

with tab3:
    st.markdown("Просьба предоставить последипломные каникулы на общий для всей выборки период.")
    faculties3, directions3, programs3 = scope_widgets(sid, key_prefix="stmt_vac")
    col1, col2, col3 = st.columns(3)
    with col1:
        date3 = st.date_input("Дата заявления", value=date(2026, 3, 15), key="stmt_vac_date")
    with col2:
        vac_start = st.date_input("Каникулы: начало", value=date(2026, 8, 1), key="stmt_vac_start")
    with col3:
        vac_end = st.date_input("Каникулы: конец", value=date(2026, 8, 28), key="stmt_vac_end")
    if st.button("🚀 Сгенерировать", type="primary", key="stmt_vac_btn"):
        with st.spinner("Собираю заявления…"):
            res = statements.generate_vacation(
                date_str=c.date_to_order_string(date3),
                start_date=c.date_to_order_string(vac_start),
                end_date=c.date_to_order_string(vac_end),
                faculties=faculties3, directions=directions3, programs=programs3, spreadsheet_id=sid,
            )
        download_results(res, key_prefix="stmt_vac", zip_name="Заявления — последипломные каникулы")

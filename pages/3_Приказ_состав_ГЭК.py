from datetime import date

import streamlit as st

from logic import common as c
from logic import prikaz_gek
from ui_helpers import download_results, require_password, scope_widgets, sidebar_data_source

st.set_page_config(page_title="Приказ: состав ГЭК", page_icon="👥", layout="wide")
require_password()
sid = sidebar_data_source()

st.title("👥 Приказ об утверждении состава и секретарей ГЭК")
st.caption(
    "Отдельный PDF на каждое направление подготовки. Состав — из листа «ГЭК» "
    "(председатель/секретарь — флаги, остальные — члены). Уровень и направление "
    "подтягиваются из листа «2025/26» по факультету+программе."
)

faculties, directions, programs = scope_widgets(sid, key_prefix="gek")

col1, col2 = st.columns(2)
with col1:
    order_date_d = st.date_input("Дата подписания (общая для всех направлений)", value=date(2026, 4, 23))
with col2:
    order_num_start = st.number_input("Стартовый № серии", min_value=1, value=1,
                                       help="Номер = ДДММГГГГ-N, N растёт по направлениям начиная с этого числа.")

order_date_str = c.date_to_order_string(order_date_d)
st.caption(f"Пример номера первого приказа серии: {c.order_num_from_date(order_date_str, order_num_start)}")

if st.button("🚀 Сгенерировать", type="primary"):
    with st.spinner("Читаю таблицы и собираю приказы…"):
        res = prikaz_gek.generate(order_date=order_date_str, order_num_start=int(order_num_start),
                                  faculties=faculties, directions=directions, programs=programs,
                                  spreadsheet_id=sid)
    download_results(res, key_prefix="prikaz_gek")

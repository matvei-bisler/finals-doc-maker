from datetime import date

import pandas as pd
import streamlit as st

from logic import common as c
from logic import prikaz_appeal
from ui_helpers import download_results, require_password, sidebar_data_source

st.set_page_config(page_title="Приказ: апелляционная комиссия", page_icon="⚖️", layout="wide")
require_password()
sid = sidebar_data_source()

st.title("⚖️ Приказ об утверждении состава апелляционной комиссии")
st.caption("Один PDF на все направления подготовки — комиссия вузовская, не привязана к конкретной программе.")

col1, col2 = st.columns(2)
with col1:
    order_date_d = st.date_input("Дата приказа", value=date(2026, 4, 22))
with col2:
    order_num_start = st.number_input("№ приказа (порядковый в дне)", min_value=1, value=1)

st.subheader("Состав комиссии")
members_df = st.data_editor(
    pd.DataFrame(prikaz_appeal.DEFAULT_MEMBERS),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "role": st.column_config.TextColumn("Роль", help="«Председатель», «Заместитель председателя», «Член комиссии»"),
        "text": st.column_config.TextColumn("ФИО, должность"),
    },
    key="appeal_members_editor",
)

order_date_str = c.date_to_order_string(order_date_d)
st.caption(f"Номер приказа: {c.order_num_from_date(order_date_str, order_num_start)}")

if st.button("🚀 Сгенерировать", type="primary"):
    with st.spinner("Собираю приказ…"):
        res = prikaz_appeal.generate(order_date=order_date_str, order_num_start=int(order_num_start),
                                     members=members_df.to_dict("records"))
    download_results(res, key_prefix="prikaz_appeal")

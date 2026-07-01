from datetime import date

import streamlit as st

from logic import common as c
from logic import prikaz_topics
from ui_helpers import download_results, scope_widgets, sidebar_data_source

st.set_page_config(page_title="Приказ: темы и руководители ВКР", page_icon="📝", layout="wide")
sid = sidebar_data_source()

st.title("📝 Приказ об утверждении тем и руководителей ВКР")
st.caption("Один PDF с пунктами по каждому направлению/профилю/курсу — бакалавриат по коду направления, затем магистратура.")

faculties, directions, programs = scope_widgets(sid, key_prefix="topics")

col1, col2 = st.columns(2)
with col1:
    order_date_d = st.date_input("Дата приказа", value=date(2026, 3, 18))
with col2:
    order_num = st.text_input("Номер приказа", value=f"{order_date_d:%d%m%Y}-1")

order_date_str = c.date_to_order_string(order_date_d)
st.caption(f"В документе будет: «ПРИКАЗ № {order_num}» от {order_date_str}")

if st.button("🚀 Сгенерировать", type="primary"):
    with st.spinner("Читаю таблицу и собираю приказ…"):
        res = prikaz_topics.generate(order_num=order_num, order_date=order_date_str,
                                     faculties=faculties, directions=directions, programs=programs,
                                     spreadsheet_id=sid)
    download_results(res, key_prefix="prikaz_topics")

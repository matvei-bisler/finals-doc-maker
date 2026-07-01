from datetime import date

import streamlit as st

from logic import common as c
from logic import report
from ui_helpers import download_results, scope_widgets, sidebar_data_source

st.set_page_config(page_title="Отчёт председателя ГЭК", page_icon="📊", layout="wide")
sid = sidebar_data_source()

st.title("📊 Отчёт председателя ГЭК")
st.caption(
    "Отдельный PDF на каждую образовательную программу. Таблица результатов защиты, "
    "списки с отличием / неудовлетворительных / рекомендованных — строятся по заполненным "
    "оценкам и колонке «диплом с отличием» из «2025/26». Все темы считаются предложенными "
    "самими обучающимися; форма обучения — очная (можно поменять ниже)."
)

faculties, directions, programs = scope_widgets(sid, key_prefix="report")

col1, col2 = st.columns(2)
with col1:
    report_date_d = st.date_input("Дата отчёта (титульный лист)", value=date(2026, 6, 20))
with col2:
    form = st.text_input("Форма обучения", value=report.FORM_DEFAULT)

st.subheader("Приказ о составе ГЭК (для раздела 1 отчёта)")
col3, col4 = st.columns(2)
with col3:
    gek_order_date_d = st.date_input("Дата приказа о составе ГЭК", value=date(2026, 4, 23))
with col4:
    gek_order_num = st.text_input("Номер приказа о составе ГЭК", value="_____________")

if st.button("🚀 Сгенерировать", type="primary"):
    with st.spinner("Читаю таблицы и собираю отчёты…"):
        res = report.generate(
            report_date=c.date_to_order_string(report_date_d),
            gek_order_num=gek_order_num,
            gek_order_date=c.date_to_order_string(gek_order_date_d),
            form=form,
            faculties=faculties, directions=directions, programs=programs,
            spreadsheet_id=sid,
        )
    download_results(res, key_prefix="reports", zip_name="Отчёты председателя ГЭК")

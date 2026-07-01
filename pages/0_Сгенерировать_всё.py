from datetime import date

import streamlit as st

from logic import common as c
from logic import (dopusk_gia, prikaz_appeal, prikaz_gek, prikaz_schedule, prikaz_topics,
                    protocol, report, reviews, statements)
from ui_helpers import render_log, require_password, scope_widgets, sidebar_data_source

st.set_page_config(page_title="Сгенерировать всё", page_icon="🗂️", layout="wide")
require_password()
sid = sidebar_data_source()

st.title("🗂️ Сгенерировать всё разом")
st.caption(
    "Собирает все выбранные ниже типы документов за один прогон в один архив. "
    "Фильтр «Что генерировать» ограничивает выборку по факультету/направлению/программе — "
    "работает так же, как на отдельных страницах. Для документов, не привязанных к программе "
    "(апелляционная комиссия), фильтр не действует."
)

faculties, directions, programs = scope_widgets(sid, key_prefix="all")

st.divider()
st.subheader("Что включить в комплект")

col1, col2, col3, col4 = st.columns(4)
with col1:
    inc_topics = st.checkbox("📝 Темы и руководители ВКР", value=True)
    inc_dopusk = st.checkbox("✅ Допуск к ГИА", value=True)
with col2:
    inc_gek = st.checkbox("👥 Состав ГЭК", value=True)
    inc_sched = st.checkbox("🗓️ Расписание ГИА", value=True)
with col3:
    inc_appeal = st.checkbox("⚖️ Апелляционная комиссия", value=True)
    inc_protocols = st.checkbox("📄 Протоколы ГЭК", value=True)
with col4:
    inc_report = st.checkbox("📊 Отчёт председателя ГЭК", value=True)
    inc_reviews = st.checkbox("✍️ Отзывы и рецензии", value=False)

inc_statements = st.checkbox(
    "🖊️ Заявления студентов (тема ВКР + ознакомление с ГИА + последипломные каникулы)", value=True)

st.divider()
st.subheader("Реквизиты")

with st.expander("Даты и номера приказов", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        topics_date = st.date_input("Дата приказа: темы и руководители", value=date(2026, 3, 18), key="all_topics_date")
        topics_num = st.text_input("№ приказа: темы и руководители", value=f"{topics_date:%d%m%Y}-1", key="all_topics_num")
    with c2:
        gek_date = st.date_input("Дата приказа: состав ГЭК", value=date(2026, 4, 23), key="all_gek_date")
        sched_date = st.date_input("Дата приказа: расписание ГИА", value=date(2026, 4, 24), key="all_sched_date")
    with c3:
        appeal_date = st.date_input("Дата приказа: апелляционная комиссия", value=date(2026, 4, 22), key="all_appeal_date")
        days_before = st.number_input("Допуск к ГИА: рабочих дней до начала", min_value=0, max_value=10, value=2, key="all_days_before")

with st.expander("Реквизиты отчёта и заявлений", expanded=False):
    c4, c5 = st.columns(2)
    with c4:
        report_date = st.date_input("Дата отчёта председателя ГЭК", value=date(2026, 6, 20), key="all_report_date")
        gek_order_num = st.text_input("№ приказа о составе ГЭК (для текста отчёта)", value="_____________", key="all_gek_order_num_txt")
    with c5:
        statements_date = st.date_input("Дата подписания заявлений", value=date(2026, 3, 15), key="all_stmt_date")
        vac_start = st.date_input("Последипломные каникулы: начало", value=date(2026, 8, 1), key="all_vac_start")
        vac_end = st.date_input("Последипломные каникулы: конец", value=date(2026, 8, 28), key="all_vac_end")

if st.button("🚀 Сгенерировать весь комплект", type="primary"):
    master = c.GenerationResult()

    def run(name: str, folder: str, fn):
        st.write(f"⏳ {name}…")
        try:
            res = fn()
        except Exception as e:
            master.log.append(f"✗ {name}: {e}")
            master.errors.append(f"✗ {name}: {e}")
            return
        for relpath, data in res.files.items():
            master.files[f"{folder}/{relpath}"] = data
        master.log.append(f"— {name} —")
        master.log.extend(res.log)
        master.errors.extend(res.errors)

    with st.spinner("Собираю весь комплект документов — это может занять несколько минут…"):
        if inc_topics:
            run("Темы и руководители ВКР", "01_Приказ_темы_и_руководители", lambda: prikaz_topics.generate(
                order_num=topics_num, order_date=c.date_to_order_string(topics_date),
                faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))

        if inc_dopusk:
            run("Допуск к ГИА", "02_Приказ_допуск_к_ГИА", lambda: dopusk_gia.generate(
                days_before=int(days_before), courses=None,
                faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))

        if inc_gek:
            run("Состав ГЭК", "03_Приказ_состав_ГЭК", lambda: prikaz_gek.generate(
                order_date=c.date_to_order_string(gek_date),
                faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))

        if inc_sched:
            run("Расписание ГИА", "04_Приказ_расписание_ГИА", lambda: prikaz_schedule.generate(
                order_date=c.date_to_order_string(sched_date),
                faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))

        if inc_appeal:
            run("Апелляционная комиссия", "05_Приказ_апелляционная_комиссия", lambda: prikaz_appeal.generate(
                order_date=c.date_to_order_string(appeal_date)))

        if inc_protocols:
            run("Протоколы ГЭК", "06_Протоколы_ГЭК", lambda: protocol.generate(
                faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))

        if inc_report:
            run("Отчёт председателя ГЭК", "07_Отчёт_председателя_ГЭК", lambda: report.generate(
                report_date=c.date_to_order_string(report_date), gek_order_num=gek_order_num,
                gek_order_date=c.date_to_order_string(gek_date),
                faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))

        if inc_reviews:
            run("Отзывы и рецензии", "08_Отзывы_и_рецензии", lambda: reviews.generate(
                faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))

        if inc_statements:
            sd = c.date_to_order_string(statements_date)
            run("Заявления: тема ВКР", "09_Заявления/Тема_ВКР", lambda: statements.generate_topics(
                date_str=sd, faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))
            run("Заявления: ознакомление с ГИА", "09_Заявления/Ознакомление_с_ГИА", lambda: statements.generate_gia_ack(
                date_str=sd, faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))
            run("Заявления: последипломные каникулы", "09_Заявления/Последипломные_каникулы",
                lambda: statements.generate_vacation(
                    date_str=sd, start_date=c.date_to_order_string(vac_start),
                    end_date=c.date_to_order_string(vac_end),
                    faculties=faculties, directions=directions, programs=programs, spreadsheet_id=sid))

    render_log(master.log)
    if not master.files:
        st.warning("Ничего не сгенерировано — отметь хотя бы один тип документа.")
    else:
        if master.errors:
            st.error(f"Ошибок при компиляции: {len(master.errors)} (см. лог).")
        st.success(f"Готово: {len(master.files)} файл(ов) в комплекте.")

        import zipfile
        from io import BytesIO
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for relpath, data in master.files.items():
                zf.writestr(relpath, data)
        st.download_button("⬇️ Скачать весь комплект (.zip)", data=buf.getvalue(),
                            file_name="Комплект документов ГЭК.zip", mime="application/zip",
                            type="primary", key="all_zip")

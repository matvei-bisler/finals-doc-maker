import streamlit as st

from logic import protocol
from ui_helpers import download_results, require_password, scope_widgets, sidebar_data_source

st.set_page_config(page_title="Протоколы ГЭК", page_icon="📄", layout="wide")
require_password()
sid = sidebar_data_source()

st.title("📄 Протоколы заседаний ГЭК")
st.caption(
    "Индивидуальный протокол на каждого обучающегося + протокол о присвоении квалификации на "
    "каждый профиль. Сквозная нумерация по датам защиты (раньше дата → меньше номер). Если на "
    "профиль указано несколько дней защиты — обучающиеся делятся по дням поровну (по алфавиту)."
)

st.info("Нумерация протоколов — сквозная по всей выборке. Если сгенерировать только часть "
        "программ фильтром ниже, номера будут считаться заново внутри этой части, а не как "
        "продолжение общей нумерации.", icon="ℹ️")

faculties, directions, programs = scope_widgets(sid, key_prefix="protocols")

with st.expander("⚙️ Настройки формулировок", expanded=False):
    form = st.text_input("Форма обучения", value=protocol.FORM_DEFAULT)
    col1, col2 = st.columns(2)
    with col1:
        vkr_bachelor = st.text_input("Вид ВКР — бакалавриат", value=protocol.VKR_TYPE_BACHELOR)
    with col2:
        vkr_master = st.text_input("Вид ВКР — магистратура", value=protocol.VKR_TYPE_MASTER)
    stock_questions = st.text_area("Стандартные вопросы ГЭК (одинаковые для всех протоколов)",
                                    value=protocol.STOCK_QUESTIONS, height=120)
    default_defense_date = st.text_input(
        "Заготовка даты защиты (если не заполнена в «График»)",
        value="«__» ________ 2026 года",
    )

if st.button("🚀 Сгенерировать", type="primary"):
    with st.spinner("Читаю таблицы и собираю протоколы… это может занять минуту-другую (много PDF)."):
        res = protocol.generate(
            form=form, vkr_type_bachelor=vkr_bachelor, vkr_type_master=vkr_master,
            stock_questions=stock_questions, default_defense_date=default_defense_date,
            faculties=faculties, directions=directions, programs=programs,
            spreadsheet_id=sid,
        )
    download_results(res, key_prefix="protocols", zip_name="Протоколы ГЭК")

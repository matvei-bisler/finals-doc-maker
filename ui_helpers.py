"""Общие элементы Streamlit-страниц: источник данных, лог, скачивание файлов/zip."""
from __future__ import annotations

import zipfile
from io import BytesIO

import streamlit as st

from logic import common as c


def require_password():
    """Простой парольный доступ: пароль задаётся в secrets.toml как `password = "..."`.

    Если секрет не задан (например, локальная разработка), пропускает без пароля.
    Вызывать сразу после st.set_page_config(), до остального содержимого страницы.
    """
    try:
        correct_password = st.secrets.get("password")
    except Exception:
        # Секретов вообще нет (ни файла, ни настроенных secrets на Cloud) — доступ открыт.
        return
    if not correct_password:
        return
    if st.session_state.get("authenticated"):
        return

    st.title("🔒 Вход")
    with st.form("login_form"):
        entered = st.text_input("Женщина-апостол не пускает!", type="password")
        submitted = st.form_submit_button("Войти")
    if submitted:
        if entered == correct_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Я тебя не боюсь, тварь!")
    st.stop()


def get_spreadsheet_id() -> str:
    return st.session_state.get("spreadsheet_id", c.DEFAULT_SPREADSHEET_ID)


def sidebar_data_source(extra_sheets: list[str] | None = None) -> str:
    """Показывает ссылку на таблицу и список вкладок. Возвращает текущий spreadsheet_id."""
    st.sidebar.markdown("### 📊 Источник данных")
    sid = st.sidebar.text_input(
        "ID Google-таблицы", value=get_spreadsheet_id(), key="spreadsheet_id",
        help="Из ссылки: docs.google.com/spreadsheets/d/**ЭТОТ_ID**/edit",
    )
    st.sidebar.markdown(f"🔗 [Открыть таблицу «ВКР UU»↗]({c.sheet_url(sid)})")
    sheets = [c.SHEET_STUDENTS, c.SHEET_GEK, c.SHEET_SCHEDULE, "Руководители", "Рецензенты", c.SHEET_REGISTRY]
    if extra_sheets:
        sheets += [s for s in extra_sheets if s not in sheets]
    with st.sidebar.expander("Вкладки, которые используются"):
        for name in sheets:
            st.markdown(f"- «{name}»")
    st.sidebar.caption("Таблица должна быть открыта «для всех, у кого есть ссылка».")
    return sid


def scope_widgets(spreadsheet_id: str, key_prefix: str = "scope"):
    """Мультиселекты факультет/направление/программа — для генерации не всего, а по кусочкам.

    Возвращает (faculties, directions, programs) — каждый список или None (=без фильтра),
    если пользователь ничего не выбрал (значит «всё»).
    """
    try:
        rows = c.fetch_sheet_rows(c.SHEET_STUDENTS, spreadsheet_id)
        facets = c.unique_facets(rows)
    except Exception as e:
        st.warning(f"Не удалось прочитать список факультетов/направлений/программ: {e}")
        facets = {"faculties": [], "directions": [], "programs": []}

    with st.expander("🎯 Что генерировать — всё или выборочно", expanded=False):
        st.caption("Ничего не выбрано в фильтре = генерируется для всех.")
        col1, col2, col3 = st.columns(3)
        with col1:
            faculties = st.multiselect("Факультет", facets["faculties"], key=f"{key_prefix}_fac")
        with col2:
            directions = st.multiselect("Направление подготовки", facets["directions"], key=f"{key_prefix}_dir")
        with col3:
            programs = st.multiselect("Профиль (программа)", facets["programs"], key=f"{key_prefix}_prog")

    return (faculties or None, directions or None, programs or None)


def render_log(log: list[str]):
    if not log:
        return
    with st.expander("Лог генерации", expanded=True):
        st.code("\n".join(log), language=None)


def download_results(res: "c.GenerationResult", key_prefix: str, zip_name: str | None = None):
    """Кнопка «скачать всё zip» + разворачиваемый список отдельных файлов."""
    render_log(res.log)

    if not res.files:
        st.warning("Файлы не созданы — проверьте лог выше.")
        return

    if res.errors:
        st.error(f"Ошибок при компиляции: {len(res.errors)} (см. лог).")

    st.success(f"Готово: {len(res.files)} файл(ов).")

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for relpath, data in res.files.items():
            zf.writestr(relpath, data)
    st.download_button(
        "⬇️ Скачать всё одним архивом (.zip)",
        data=buf.getvalue(),
        file_name=f"{zip_name or key_prefix}.zip",
        mime="application/zip",
        key=f"{key_prefix}_zip",
        type="primary",
    )

    with st.expander(f"Отдельные файлы ({len(res.files)})"):
        for relpath, data in res.files.items():
            st.download_button(
                f"⬇️ {relpath}", data=data, file_name=relpath.split("/")[-1],
                mime="application/pdf", key=f"{key_prefix}_{relpath}",
            )

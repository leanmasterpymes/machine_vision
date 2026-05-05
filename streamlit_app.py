import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from app.excel import build_workbook_bytes
from app.vision import extract_sheet

load_dotenv()

st.set_page_config(page_title="machine_vision", page_icon=None, layout="wide")
st.title("machine_vision")
st.caption("Sube una hoja escaneada, revisa/edita el contenido y descarga el Excel.")

uploaded = st.file_uploader(
    "Imagen de la hoja",
    type=["png", "jpg", "jpeg", "webp", "gif"],
    accept_multiple_files=False,
)

col_img, col_data = st.columns([1, 1])

if uploaded is not None:
    with col_img:
        st.image(uploaded, caption=uploaded.name, use_container_width=True)

    if st.button("Extraer contenido", type="primary"):
        with st.spinner("Procesando imagen..."):
            suffix = Path(uploaded.name).suffix.lower() or ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = Path(tmp.name)
            try:
                data = extract_sheet(tmp_path)
            except Exception as e:
                st.error(f"Error en extraccion: {e}")
                st.stop()
            finally:
                tmp_path.unlink(missing_ok=True)

        headers = data.get("headers") or []
        rows = data.get("rows") or []
        if headers:
            df = pd.DataFrame(rows, columns=headers)
        else:
            df = pd.DataFrame(rows)
        st.session_state["df"] = df
        st.session_state["title"] = data.get("title") or ""
        st.session_state["notes"] = data.get("notes") or ""

if "df" in st.session_state:
    with col_data:
        st.subheader("Tabla extraida (editable)")
        st.session_state["title"] = st.text_input("Titulo", st.session_state.get("title", ""))
        edited = st.data_editor(
            st.session_state["df"],
            num_rows="dynamic",
            use_container_width=True,
            key="editor",
        )
        st.session_state["notes"] = st.text_area(
            "Notas",
            st.session_state.get("notes", ""),
            help="Observaciones del modelo sobre celdas ilegibles o ambiguas.",
        )

        xlsx_bytes = build_workbook_bytes(
            edited,
            title=st.session_state["title"] or None,
            notes=st.session_state["notes"] or None,
        )
        st.download_button(
            "Descargar Excel",
            data=xlsx_bytes,
            file_name="hoja.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

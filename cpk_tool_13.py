import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ===============================
# CONFIG
# ===============================
st.set_page_config(layout="wide")

st.title("🏭 SPC CPK Tool - Production Version")
st.markdown("### CPK_Tool_AGS_Quality_First")

# ===============================
# FUNCIONES
# ===============================
def limpiar_columna(series):
    series = series.astype(str)
    series = series.str.replace(",", ".", regex=False)
    return pd.to_numeric(series, errors="coerce")

def detectar_columna(columnas, keywords):
    for col in columnas:
        col_low = col.lower()
        for key in keywords:
            if key in col_low:
                return col
    return None

# ===============================
# SESSION STATE INIT
# ===============================
if "df_res" not in st.session_state:
    st.session_state.df_res = None

if "df" not in st.session_state:
    st.session_state.df = None

if "cols" not in st.session_state:
    st.session_state.cols = {}

# ===============================
# UPLOAD
# ===============================
archivo = st.file_uploader("📂 Upload Excel file")

if archivo:

    df = pd.read_excel(archivo)

    st.session_state.df = df

    st.subheader("🔍 Preview Data")
    st.dataframe(df.head())

    columnas = df.columns

    col_test = detectar_columna(columnas, ["test step name"])
    col_val  = detectar_columna(columnas, ["test value number"])
    col_lsl  = detectar_columna(columnas, ["lsl"])
    col_usl  = detectar_columna(columnas, ["usl"])

    st.session_state.cols = {
        "test": col_test,
        "val": col_val,
        "lsl": col_lsl,
        "usl": col_usl
    }

    st.subheader("🔎 Columnas detectadas")
    st.write(st.session_state.cols)

    if None in st.session_state.cols.values():
        st.error("❌ Error detectando columnas")
        st.stop()

    # LIMPIEZA
    df[col_test] = df[col_test].astype(str).str.strip()
    df[col_val] = limpiar_columna(df[col_val])
    df[col_lsl] = limpiar_columna(df[col_lsl])
    df[col_usl] = limpiar_columna(df[col_usl])

    df = df.dropna(subset=[col_val])

    st.session_state.df = df

# ===============================
# CPK CALC
# ===============================
if st.button("🚀 Calcular CPK") and st.session_state.df is not None:

    df = st.session_state.df
    col_test = st.session_state.cols["test"]
    col_val = st.session_state.cols["val"]
    col_lsl = st.session_state.cols["lsl"]
    col_usl = st.session_state.cols["usl"]

    resultados = []

    for step, grupo in df.groupby(col_test):

        valores = grupo[col_val].dropna().values

        if len(valores) == 0:
            continue

        avg = np.mean(valores)
        std = np.std(valores, ddof=1) if len(valores) > 1 else 0

        lsl = grupo[col_lsl].iloc[0]
        usl = grupo[col_usl].iloc[0]

        if std == 0 or len(valores) < 2:
            cpl = cpu = cpk = None
            comentario = f"Pocos datos ({len(valores)})"
        else:
            cpl = (avg - lsl) / (3 * std)
            cpu = (usl - avg) / (3 * std)
            cpk = min(cpl, cpu)
            comentario = ""

        status = "⚪" if cpk is None else ("🔴" if cpk < 1.33 else "🟢")

        resultados.append([
            step, len(valores),
            lsl, usl,
            avg, std,
            cpl, cpu, cpk,
            status, comentario
        ])

    st.session_state.df_res = pd.DataFrame(resultados, columns=[
        "Test Step","N",
        "LSL","USL",
        "Average","Stdev",
        "CPL","CPU","CPK",
        "Status","Comentario"
    ])

# ===============================
# RESULTADOS
# ===============================
if st.session_state.df_res is not None:

    df_res = st.session_state.df_res
    df = st.session_state.df
    col_test = st.session_state.cols["test"]
    col_val = st.session_state.cols["val"]
    col_lsl = st.session_state.cols["lsl"]
    col_usl = st.session_state.cols["usl"]

    st.subheader("📊 CPK Results")
    st.dataframe(df_res)

    # ===============================
    # GRAFICAS
    # ===============================
    st.subheader("📈 Graficar múltiples Test Steps")

    seleccion = st.multiselect(
        "Selecciona Test Steps",
        df_res["Test Step"]
    )

    if st.button("📊 Generar gráficas"):

        for step_sel in seleccion:

            subset = df[df[col_test] == step_sel]

            if subset.empty:
                continue

            y = subset[col_val].values
            x = np.arange(1, len(y) + 1)

            lsl = subset[col_lsl].iloc[0]
            usl = subset[col_usl].iloc[0]

            fig, ax = plt.subplots(figsize=(10,4))

            ax.scatter(x, y)
            ax.axhline(lsl)
            ax.axhline(usl)

            ax.set_title(step_sel)
            ax.grid(True)

            st.pyplot(fig)

    # ===============================
    # PDF EXPORT
    # ===============================
    st.subheader("📄 Export Report")

    if st.button("📄 Exportar PDF"):

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        c = canvas.Canvas(temp_pdf.name, pagesize=letter)

        width, height = letter
        fecha = datetime.now().strftime("%Y-%m-%d")

        # LOGO (seguro)
        if os.path.exists("logo.png"):
            c.drawImage("logo.png", 50, height - 80, width=150, height=40)

        # TITULO
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 110, "CPK Analysis Report")

        c.setFont("Helvetica", 9)
        c.drawString(50, height - 125, f"Date: {fecha}")

        y_pos = height - 150

        # TABLA
        for _, row in df_res.iterrows():

            linea = f"{row['Test Step'][:40]} | N={row['N']} | CPK={row['CPK']}"
            c.drawString(50, y_pos, linea)

            y_pos -= 12
            if y_pos < 60:
                c.showPage()
                y_pos = height - 50

        # FIRMA
        c.setFont("Helvetica-Oblique", 9)
        c.drawRightString(550, 30, f"Report by Francisco Leyva | {fecha}")

        c.save()

        with open(temp_pdf.name, "rb") as f:
            pdf_bytes = f.read()

        st.download_button(
            "⬇ Descargar PDF",
            data=pdf_bytes,
            file_name="CPK_Report.pdf",
            mime="application/pdf"
        )
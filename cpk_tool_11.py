import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import tempfile
import io
from datetime import datetime

st.set_page_config(layout="wide")

# ===============================
# TITULO
# ===============================
st.title("🏭 CPK_Tool_AGS_Quality_First_")
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
# SESSION STATE
# ===============================
if "df_res" not in st.session_state:
    st.session_state.df_res = None

# ===============================
# UPLOAD
# ===============================
archivo = st.file_uploader("📂 Upload Excel file")

if archivo:

    df = pd.read_excel(archivo)

    st.subheader("🔍 Preview Data")
    st.dataframe(df.head())

    columnas = df.columns

    col_test = detectar_columna(columnas, ["test step name"])
    col_val  = detectar_columna(columnas, ["test value number"])
    col_lsl  = detectar_columna(columnas, ["lsl"])
    col_usl  = detectar_columna(columnas, ["usl"])

    st.subheader("🔎 Columnas detectadas")
    st.write({
        "Test Step": col_test,
        "Measurement": col_val,
        "LSL": col_lsl,
        "USL": col_usl
    })

    if None in [col_test, col_val, col_lsl, col_usl]:
        st.error("❌ Error detectando columnas")
        st.stop()

    # ===============================
    # LIMPIEZA
    # ===============================
    df[col_test] = df[col_test].astype(str).str.strip()
    df[col_val] = limpiar_columna(df[col_val])
    df[col_lsl] = limpiar_columna(df[col_lsl])
    df[col_usl] = limpiar_columna(df[col_usl])

    df = df.dropna(subset=[col_val])

    # ===============================
    # CALCULO CPK
    # ===============================
    if st.button("🚀 Calcular CPK"):

        resultados = []

        for step, grupo in df.groupby(col_test):

            valores = grupo[col_val].dropna().values

            if len(valores) == 0:
                continue

            avg = np.mean(valores)

            if len(valores) > 1:
                std = np.std(valores, ddof=1)
            else:
                std = 0

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

            if cpk is None:
                status = "⚪"
            elif cpk < 1.33:
                status = "🔴"
            else:
                status = "🟢"

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
# RESULTADOS + GRAFICAS + PDF
# ===============================
if st.session_state.df_res is not None:

    df_res = st.session_state.df_res

    st.subheader("📊 CPK Results")
    st.dataframe(df_res)

    df_valid = df_res[df_res["N"] > 0]

    # ===============================
    # GRAFICAS
    # ===============================
    st.subheader("📈 Graficar múltiples Test Steps")

    seleccion = st.multiselect(
        "Selecciona Test Steps",
        df_valid["Test Step"]
    )

    if st.button("📊 Generar gráficas"):

        for step_sel in seleccion:

            subset = df[df[col_test] == step_sel]

            y = subset[col_val].values
            x = np.arange(1, len(y) + 1)

            lsl = subset[col_lsl].iloc[0]
            usl = subset[col_usl].iloc[0]

            fig, ax = plt.subplots(figsize=(10,4))

            ax.scatter(x, y, color="red", edgecolors="blue")
            ax.axhline(y=lsl, color="blue", label="LSL")
            ax.axhline(y=usl, color="blue", linestyle="--", label="USL")

            ax.set_title(step_sel)
            ax.grid(True)
            ax.legend()

            st.pyplot(fig)

    # ===============================
    # EXPORTAR PDF
    # ===============================
    st.subheader("📄 Exportar reporte")

    if st.button("📄 Exportar PDF"):

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        c = canvas.Canvas(temp_pdf.name, pagesize=letter)
        width, height = letter

        # LOGO
        try:
            c.drawImage("logo.png", 50, height - 80, width=180, height=50)
        except:
            pass

        # TITULO
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 120, "CPK Analysis Report")

        fecha = datetime.now().strftime("%Y-%m-%d")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 140, f"Date: {fecha}")

        y_pos = height - 170

        c.setFont("Helvetica", 8)

        for _, row in df_res.iterrows():

            linea = f"{row['Test Step'][:40]} | N={row['N']} | CPK={row['CPK']} | {row['Status']}"
            c.drawString(50, y_pos, linea)

            y_pos -= 12

            if y_pos < 80:
                c.showPage()
                y_pos = height - 50

        # FIRMA
        c.setFont("Helvetica-Oblique", 10)
        firma = f"Report generated by Francisco Leyva | {fecha}"
        c.drawRightString(550, 30, firma)

        c.save()

        with open(temp_pdf.name, "rb") as f:
            st.download_button(
                "⬇ Descargar PDF",
                data=f,
                file_name="CPK_Report.pdf",
                mime="application/pdf"
            )
``
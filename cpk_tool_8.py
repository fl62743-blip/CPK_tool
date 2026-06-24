import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🏭 CPK Analysis Tool (Auto Detect)")

# ===============================
# LIMPIEZA
# ===============================
def limpiar_columna(series):
    series = series.astype(str)
    series = series.str.replace(",", ".", regex=False)
    series = series.str.strip()
    return pd.to_numeric(series, errors="coerce")

# ===============================
# DETECCION AUTOMATICA
# ===============================
def detectar_columna(columns, keywords):

    for col in columns:
        col_lower = col.lower()
        for key in keywords:
            if key in col_lower:
                return col

    return None

# ===============================
# UPLOAD
# ===============================
archivo = st.file_uploader("📂 Upload Excel file")

if archivo:

    df = pd.read_excel(archivo)

    st.subheader("🔍 Preview Data")
    st.dataframe(df.head())

    columnas = df.columns

    # ===============================
    # AUTODETECCION
    # ===============================
    col_test = detectar_columna(columnas, ["test step", "step name", "testname"])
    col_val  = detectar_columna(columnas, ["value", "measurement", "result"])
    col_lsl  = detectar_columna(columnas, ["lsl", "low"])
    col_usl  = detectar_columna(columnas, ["usl", "high"])

    # Mostrar detección
    st.subheader("🔎 Columnas detectadas")

    st.write({
        "Test Step": col_test,
        "Measurement": col_val,
        "LSL": col_lsl,
        "USL": col_usl
    })

    # ✅ Verificar si encontró todo
    if None in [col_test, col_val, col_lsl, col_usl]:

        st.warning("⚠ No se detectaron todas las columnas automáticamente")

        col_test = st.selectbox("Selecciona Test Step", columnas)
        col_val  = st.selectbox("Selecciona Measurement", columnas)
        col_lsl  = st.selectbox("Selecciona LSL", columnas)
        col_usl  = st.selectbox("Selecciona USL", columnas)

    # ===============================
    # RUN
    # ===============================
    if st.button("🚀 Calcular CPK"):

        # Limpieza
        df[col_test] = df[col_test].astype(str).str.strip()
        df[col_val] = limpiar_columna(df[col_val])
        df[col_lsl] = limpiar_columna(df[col_lsl])
        df[col_usl] = limpiar_columna(df[col_usl])

        df = df.dropna(subset=[col_test, col_val])

        resultados = []

        for step, grupo in df.groupby(col_test):

            valores = grupo[col_val].values

            if len(valores) < 2:
                continue

            avg = np.mean(valores)
            std = np.std(valores, ddof=1)

            lsl = grupo[col_lsl].iloc[0]
            usl = grupo[col_usl].iloc[0]

            if lsl == usl:
                cpl = cpu = cpk = None
                comentario = "LSL = USL"
            elif std == 0:
                cpl = cpu = cpk = None
                comentario = "Stdev = 0"
            else:
                cpl = (avg - lsl) / (3 * std)
                cpu = (usl - avg) / (3 * std)
                cpk = min(cpl, cpu)
                comentario = ""

            # SEMAFORO
            if cpk is None:
                status = "⚪"
            elif cpk < 1.33:
                status = "🔴"
            else:
                status = "🟢"

            resultados.append([
                step, lsl, usl,
                avg, std,
                cpl, cpu, cpk,
                status, comentario
            ])

        df_res = pd.DataFrame(resultados, columns=[
            "Test Step","LSL","USL","Average","Stdev",
            "CPL","CPU","CPK","Status","Comentario"
        ])

        st.subheader("📊 CPK Results")
        st.dataframe(df_res)

        # ===============================
        # GRAFICA
        # ===============================
        st.subheader("📈 Graficar Test Step")

        step_sel = st.selectbox("Selecciona Test Step", df_res["Test Step"])

        if step_sel:

            subset = df[df[col_test] == step_sel]

            y = subset[col_val].values
            x = np.arange(1, len(y)+1)

            lsl = subset[col_lsl].iloc[0]
            usl = subset[col_usl].iloc[0]

            fig, ax = plt.subplots(figsize=(10,5))

            ax.set_facecolor("#f2f2f2")

            ax.scatter(x, y, color="red", edgecolors="blue")

            ax.axhline(y=lsl, color="blue", label="LSL")
            ax.axhline(y=usl, color="blue", linestyle="--", label="USL")

            ax.set_title(step_sel)
            ax.set_xlabel("Sample Index")
            ax.set_ylabel("Measurement")

            ax.grid(True)
            ax.legend()

            st.pyplot(fig)

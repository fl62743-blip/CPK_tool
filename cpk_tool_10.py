import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🏭 SPC CPK Tool - Final Stable Version")

# ===============================
# LIMPIEZA NUMERICA
# ===============================
def limpiar_columna(series):
    series = series.astype(str)
    series = series.str.replace(",", ".", regex=False)
    return pd.to_numeric(series, errors="coerce")

# ===============================
# DETECCIÓN AUTOMÁTICA
# ===============================
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

    # ===============================
    # AUTO-DETECCION (ajustada a tu archivo)
    # ===============================
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
        st.error("❌ No se detectaron columnas correctamente")
        st.stop()

    # ===============================
    # LIMPIEZA
    # ===============================
    df[col_test] = df[col_test].astype(str).str.strip()
    df[col_val] = limpiar_columna(df[col_val])
    df[col_lsl] = limpiar_columna(df[col_lsl])
    df[col_usl] = limpiar_columna(df[col_usl])

    # solo eliminar medición inválida
    df = df.dropna(subset=[col_val])

    # ===============================
    # BOTON CALCULO CPK
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

            # ===============================
            # CPK
            # ===============================
            if std == 0 or len(valores) < 2:
                cpl = cpu = cpk = None
                comentario = f"Pocos datos ({len(valores)})"
            else:
                cpl = (avg - lsl) / (3 * std)
                cpu = (usl - avg) / (3 * std)
                cpk = min(cpl, cpu)
                comentario = ""

            # ===============================
            # SEMAFORO
            # ===============================
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
# MOSTRAR RESULTADOS
# ===============================
if st.session_state.df_res is not None:

    df_res = st.session_state.df_res

    st.subheader("📊 CPK Results")
    st.dataframe(df_res)

    df_valid = df_res[df_res["N"] > 0]

    # ===============================
    # GRAFICAS MULTIPLES
    # ===============================
    st.subheader("📈 Graficar múltiples Test Steps")

    seleccion = st.multiselect(
        "Selecciona uno o más Test Steps",
        df_valid["Test Step"]
    )

    # BOTON INDEPENDIENTE
    if st.button("📊 Generar gráficas"):

        if len(seleccion) == 0:
            st.warning("Selecciona al menos un Test Step")

        else:

            for step_sel in seleccion:

                subset = df[df[col_test] == step_sel]

                y = subset[col_val].values
                x = np.arange(1, len(y)+1)

                lsl = subset[col_lsl].iloc[0]
                usl = subset[col_usl].iloc[0]

                fig, ax = plt.subplots(figsize=(10,4))

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

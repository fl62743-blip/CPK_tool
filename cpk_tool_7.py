import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🏭 CPK Analysis Tool")

# ===============================
# FUNCION LIMPIEZA
# ===============================
def limpiar_columna(series):
    series = series.astype(str)
    series = series.str.replace(",", ".", regex=False)
    series = series.str.strip()
    return pd.to_numeric(series, errors="coerce")

# ===============================
# 1. SUBIR ARCHIVO
# ===============================
archivo = st.file_uploader("📂 Upload Excel file")

if archivo is not None:

    df = pd.read_excel(archivo, sheet_name="Sheet1")

    st.subheader("🔍 Preview Data")
    st.dataframe(df.head())

    # ===============================
    # 2. VALIDAR COLUMNAS
    # ===============================
    columnas_requeridas = ["O", "U", "V", "W"]

    if not all(col in df.columns for col in columnas_requeridas):
        st.error("❌ El archivo debe contener columnas O, U, V, W")
        st.stop()

    # ===============================
    # 3. LIMPIEZA
    # ===============================
    df["O"] = df["O"].astype(str).str.strip()
    df["W"] = limpiar_columna(df["W"])
    df["U"] = limpiar_columna(df["U"])
    df["V"] = limpiar_columna(df["V"])

    df = df.dropna(subset=["O", "W"])

    # ===============================
    # 4. BOTON CALCULO
    # ===============================
    if st.button("🚀 Calcular CPK"):

        resultados = []

        for step, grupo in df.groupby("O"):

            valores = grupo["W"].values

            if len(valores) < 2:
                continue

            avg = np.mean(valores)
            std = np.std(valores, ddof=1)

            lsl = grupo["U"].iloc[0]
            usl = grupo["V"].iloc[0]

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

            # ===== SEMAFORO =====
            if cpk is None:
                status = "⚪"
            elif cpk < 1.33:
                status = "🔴"
            else:
                status = "🟢"

            resultados.append([
                step, lsl, usl,
                round(avg,6),
                round(std,6),
                None if cpl is None else round(cpl,4),
                None if cpu is None else round(cpu,4),
                None if cpk is None else round(cpk,4),
                status,
                comentario
            ])

        df_res = pd.DataFrame(resultados, columns=[
            "Test Step","LSL","USL","Average","Stdev",
            "CPL","CPU","CPK","Status","Comentario"
        ])

        # ===============================
        # 5. MOSTRAR RESULTADOS
        # ===============================
        st.subheader("📊 CPK Results")
        st.dataframe(df_res)

        # ===============================
        # 6. GRAFICAR
        # ===============================
        st.subheader("📈 Graficar Test Step")

        step_sel = st.selectbox("Selecciona un Test Step", df_res["Test Step"])

        if step_sel:

            subset = df[df["O"] == step_sel]

            y = subset["W"].values
            x = np.arange(1, len(y)+1)

            lsl = subset["U"].iloc[0]
            usl = subset["V"].iloc[0]

            fig, ax = plt.subplots(figsize=(10,5))

            ax.set_facecolor("#f2f2f2")

            ax.scatter(x, y, color="red", edgecolors="blue", s=60)

            ax.axhline(y=lsl, color="blue", label="LSL")
            ax.axhline(y=usl, color="blue", linestyle="--", label="USL")

            ax.set_title(step_sel)
            ax.set_xlabel("Sample Index")
            ax.set_ylabel("Measurement")

            ax.grid(True)
            ax.legend()

            st.pyplot(fig)
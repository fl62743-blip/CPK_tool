import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🏭 SPC CPK Web Tool")

# ===============================
# FUNCION LIMPIEZA
# ===============================
def convertir_columnas(df, cols):
    for col in cols:
        df[col] = df[col].astype(str)
        df[col] = df[col].str.replace(",", ".", regex=False)
        df[col] = df[col].str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# ===============================
# FUNCION CPK
# ===============================
def calcular_cpk(df):

    resultados = []

    grupos = df.groupby("TestStep")

    for key, grupo in grupos:

        valores = grupo["Value"].dropna().values

        if len(valores) < 2:
            continue

        avg = np.mean(valores)
        stdev = np.std(valores, ddof=1)

        lsl = grupo["LSL"].iloc[0]
        usl = grupo["USL"].iloc[0]

        if lsl == usl:
            cpl = cpu = cpk = None
            comentario = "LSL = USL"

        elif stdev == 0:
            cpl = cpu = cpk = None
            comentario = "Stdev = 0"

        else:
            cpl = (avg - lsl) / (3 * stdev)
            cpu = (usl - avg) / (3 * stdev)
            cpk = min(cpl, cpu)
            comentario = ""

        # Semáforo
        if cpk is None:
            status = "⚪"
        elif cpk < 1:
            status = "🔴"
        elif cpk < 1.33:
            status = "🟡"
        else:
            status = "🟢"

        resultados.append([
            key, lsl, usl,
            round(avg,6),
            round(stdev,6),
            None if cpl is None else round(cpl,4),
            None if cpu is None else round(cpu,4),
            None if cpk is None else round(cpk,4),
            status,
            comentario
        ])

    cols = ["Test Step","LSL","USL","Average","Stdev.S","CPL","CPU","CPK","Status","Comentario"]

    return pd.DataFrame(resultados, columns=cols)

# ===============================
# UPLOAD
# ===============================
file = st.file_uploader("📂 Upload Excel file")

if file:

    df = pd.read_excel(file)

    st.subheader("🔍 Preview")
    st.dataframe(df.head())

    # ===============================
    # SELECCION COLUMNAS
    # ===============================
    st.subheader("⚙ Selecciona columnas")

    col_test = st.selectbox("Test Step", df.columns)
    col_val  = st.selectbox("Measurement", df.columns)
    col_lsl  = st.selectbox("LSL", df.columns)
    col_usl  = st.selectbox("USL", df.columns)

    if col_test and col_val and col_lsl and col_usl:

        # Renombrar
        df = df.rename(columns={
            col_test: "TestStep",
            col_val: "Value",
            col_lsl: "LSL",
            col_usl: "USL"
        })

        # Limpieza tipo VBA
        df = convertir_columnas(df, ["Value","LSL","USL"])
        df["TestStep"] = df["TestStep"].astype(str).str.strip()

        df = df.dropna(subset=["TestStep","Value"])

        # ===============================
        # CPK
        # ===============================
        st.subheader("📊 CPK Results")

        df_res = calcular_cpk(df)
        st.dataframe(df_res)

        # ===============================
        # SELECT TEST STEP
        # ===============================
        st.subheader("📈 Graficar Test Step")

        steps = df_res["Test Step"].tolist()

        selected = st.selectbox("Selecciona Test Step", steps)

        if selected:

            subset = df[df["TestStep"] == selected]

            y = subset["Value"].values
            x = np.arange(1, len(y) + 1)

            lsl = subset["LSL"].iloc[0]
            usl = subset["USL"].iloc[0]

            # ===============================
            # GRAFICA
            # ===============================
            fig, ax = plt.subplots(figsize=(10,5))

            # Fondo tipo Excel
            ax.set_facecolor('#f2f2f2')

            # puntos
            ax.scatter(x, y, color='red', edgecolors='blue', s=60)

            # limites
            ax.axhline(y=lsl, color='blue', linewidth=2, label="LSL")
            ax.axhline(y=usl, color='blue', linestyle='--', linewidth=2, label="USL")

            # titulo
            ax.set_title(selected, fontsize=14)
            ax.set_xlabel("Sample Index")
            ax.set_ylabel("Measurement")

            ax.grid(True)
            ax.legend()

            st.pyplot(fig)
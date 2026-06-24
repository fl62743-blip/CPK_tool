import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 CPK Tool Web")

# ===============================
# FUNCION CONVERSION
# ===============================
def convertir_columnas(df):
    for col in ["W", "U", "V"]:
        df[col] = df[col].astype(str)
        df[col] = df[col].str.replace(",", ".", regex=False)
        df[col] = df[col].str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# ===============================
# CALCULO CPK
# ===============================
def calcular_cpk(df):

    resultados = []

    grupos = df.groupby("O")

    for key, grupo in grupos:

        valores = grupo["W"].dropna().values

        if len(valores) < 2:
            continue

        avg = np.mean(valores)
        stdev = np.std(valores, ddof=1)

        lsl = grupo["U"].iloc[0]
        usl = grupo["V"].iloc[0]

        if lsl == usl:
            cpk = None
            comentario = "LSL = USL"

        elif stdev == 0:
            cpk = None
            comentario = "Stdev = 0"

        else:
            cpk = min((avg-lsl)/(3*stdev), (usl-avg)/(3*stdev))
            comentario = ""

        resultados.append([key, avg, stdev, cpk, comentario])

    return pd.DataFrame(resultados, columns=["Test Step","Avg","Std","CPK","Comentario"])

# ===============================
# UPLOAD
# ===============================
file = st.file_uploader("Upload Excel file")

if file:

    df = pd.read_excel(file)

    st.subheader("Preview")
    st.dataframe(df.head())

    # VALIDAR COLUMNAS
    if not all(col in df.columns for col in ["O","W","U","V"]):
        st.error("File must contain columns O, W, U, V")
    
    else:

        df = convertir_columnas(df)
        df["O"] = df["O"].astype(str).str.strip()
        df = df.dropna(subset=["O","W"])

        # ===============================
        # CPK
        # ===============================
        st.subheader("CPK Results")

        df_res = calcular_cpk(df)

        st.dataframe(df_res)

        # ===============================
        # SELECT TEST STEP
        # ===============================
        steps = df_res["Test Step"].unique()

        test = st.selectbox("Select Test Step to Plot", steps)

        if test:

            subset = df[df["O"] == test]

            y = subset["W"].values
            x = np.arange(1, len(y)+1)

            lsl = subset["U"].iloc[0]
            usl = subset["V"].iloc[0]

            # ===============================
            # PLOT
            # ===============================
            fig, ax = plt.subplots(figsize=(10,5))

            ax.scatter(x, y, color='red', edgecolors='blue')

            ax.axhline(y=lsl, color='blue', label="LSL")
            ax.axhline(y=usl, color='blue', linestyle='--', label="USL")

            ax.set_title(test)
            ax.set_xlabel("Sample Index")
            ax.set_ylabel("Measurement")

            ax.grid(True)
            ax.legend()

            st.pyplot(fig)
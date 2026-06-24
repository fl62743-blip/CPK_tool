import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🏭 SPC PRO Dashboard")

# ===============================
# UPLOAD
# ===============================
file = st.file_uploader("Upload Excel File", type=["xlsx"])

if file:

    df = pd.read_excel(file)

    st.subheader("Preview Data")
    st.dataframe(df.head())

    # ===============================
    # MAPEO COLUMNAS
    # ===============================
    st.subheader("Map Columns (REQUIRED)")

    col_test = st.selectbox("Test Step column", [""] + list(df.columns))
    col_val = st.selectbox("Measurement column", [""] + list(df.columns))
    col_lsl = st.selectbox("LSL column", [""] + list(df.columns))
    col_usl = st.selectbox("USL column", [""] + list(df.columns))

    # 🚨 IMPORTANTE: no ejecutar nada si no están seleccionadas
    if col_test and col_val and col_lsl and col_usl:

        df = df.rename(columns={
            col_test: "TestStep",
            col_val: "Value",
            col_lsl: "LSL",
            col_usl: "USL"
        })

        # Limpieza segura
        df["TestStep"] = df["TestStep"].astype(str).str.strip()
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
        df["LSL"] = pd.to_numeric(df["LSL"], errors="coerce")
        df["USL"] = pd.to_numeric(df["USL"], errors="coerce")

        # Fecha opcional
        if "C" in df.columns:
            df["C"] = pd.to_datetime(df["C"], errors="coerce")

        df = df.dropna(subset=["TestStep", "Value"])

        steps = sorted(df["TestStep"].unique())

        # ===============================
        # MENU
        # ===============================
        option = st.sidebar.radio(
            "Select Module",
            [
                "🔥 Full Analysis",
                "📋 CPK Table",
                "📊 Dot Plot",
                "📈 Xbar-R",
                "⏱ Trend"
            ]
        )

        # ===============================
        # FUNCION CPK
        # ===============================
        def calcular_cpk(data, lsl, usl):
            avg = np.mean(data)
            std = np.std(data, ddof=1)

            if std == 0 or lsl == usl:
                return avg, std, np.nan

            cpl = (avg - lsl) / (3 * std)
            cpu = (usl - avg) / (3 * std)

            return avg, std, min(cpl, cpu)

        # ===============================
        # FULL ANALYSIS
        # ===============================
        if option == "🔥 Full Analysis":

            selected = st.multiselect("Select Steps", steps)

            if selected:

                col1, col2 = st.columns([1, 2])

                results = []

                for step in selected:
                    subset = df[df["TestStep"] == step]

                    data = subset["Value"].values
                    lsl = subset["LSL"].iloc[0]
                    usl = subset["USL"].iloc[0]

                    if len(data) < 2:
                        continue

                    avg, std, cpk = calcular_cpk(data, lsl, usl)

                    results.append([step, avg, std, cpk])

                with col1:
                    st.dataframe(pd.DataFrame(results, columns=["Step", "Avg", "Std", "CPK"]))

                with col2:
                    for step in selected:
                        subset = df[df["TestStep"] == step]

                        fig = px.scatter(subset, x=subset.index, y="Value", title=step)
                        fig.add_hline(y=subset["LSL"].iloc[0], line_dash="dash")
                        fig.add_hline(y=subset["USL"].iloc[0], line_dash="dash")

                        st.plotly_chart(fig, use_container_width=True)

        # ===============================
        # CPK TABLE
        # ===============================
        elif option == "📋 CPK Table":

            results = []

            for step in steps:

                subset = df[df["TestStep"] == step]

                if len(subset) < 2:
                    continue

                avg, std, cpk = calcular_cpk(
                    subset["Value"],
                    subset["LSL"].iloc[0],
                    subset["USL"].iloc[0]
                )

                status = "✅" if cpk >= 1.33 else "⚠" if cpk >= 1 else "❌"

                results.append([step, avg, std, cpk, status])

            st.dataframe(pd.DataFrame(results, columns=["Step", "Avg", "Std", "CPK", "Status"]))

    else:
        st.warning("⚠ Please select all required columns before continuing")
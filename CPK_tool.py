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
    # MAPEO DE COLUMNAS (SOLUCION AL ERROR)
    # ===============================
    st.subheader("Map Columns (Required)")

    col_test = st.selectbox("Test Step column", df.columns)
    col_val = st.selectbox("Measurement column", df.columns)
    col_lsl = st.selectbox("LSL column", df.columns)
    col_usl = st.selectbox("USL column", df.columns)

    # Renombrar
    df = df.rename(columns={
        col_test: "TestStep",
        col_val: "Value",
        col_lsl: "LSL",
        col_usl: "USL"
    })

    # Limpieza
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
    # SIDEBAR MENU
    # ===============================
    option = st.sidebar.radio(
        "Select Module",
        [
            "🔥 Full Analysis",
            "📋 CPK Table",
            "⚠ Low CPK (<1.33)",
            "📊 Manual Dot Plot",
            "📈 Xbar-R Chart",
            "⏱ Trend Chart"
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

        selected = st.multiselect("Select Test Steps", steps)

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

                results.append([step, avg, std, lsl, usl, cpk])

            res_df = pd.DataFrame(results, columns=["Step", "Avg", "Std", "LSL", "USL", "CPK"])

            with col1:
                st.dataframe(res_df)

            with col2:
                for step in selected:
                    subset = df[df["TestStep"] == step]

                    fig = px.scatter(
                        subset,
                        x=subset.index,
                        y="Value",
                        title=step
                    )

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

            status = "✅ Good" if cpk >= 1.33 else "⚠ Warning" if cpk >= 1 else "❌ Bad"

            results.append([step, avg, std, cpk, status])

        st.dataframe(pd.DataFrame(results, columns=["Step", "Avg", "Std", "CPK", "Status"]))

    # ===============================
    # LOW CPK
    # ===============================
    elif option == "⚠ Low CPK (<1.33)":

        for step in steps:
            subset = df[df["TestStep"] == step]

            if len(subset) < 2:
                continue

            avg, std, cpk = calcular_cpk(
                subset["Value"],
                subset["LSL"].iloc[0],
                subset["USL"].iloc[0]
            )

            if cpk < 1.33:

                fig = px.scatter(subset, x=subset.index, y="Value", title=f"{step} | CPK={round(cpk,2)}")

                fig.add_hline(y=subset["LSL"].iloc[0], line_dash="dash")
                fig.add_hline(y=subset["USL"].iloc[0], line_dash="dash")

                st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # MANUAL DOTPLOT
    # ===============================
    elif option == "📊 Manual Dot Plot":

        step = st.selectbox("Select Step", steps)

        subset = df[df["TestStep"] == step]

        fig = px.scatter(subset, x=subset.index, y="Value", title=step)

        fig.add_hline(y=subset["LSL"].iloc[0], line_dash="dash")
        fig.add_hline(y=subset["USL"].iloc[0], line_dash="dash")

        st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # XBAR-R
    # ===============================
    elif option == "📈 Xbar-R Chart":

        step = st.selectbox("Select Step", steps)

        data = df[df["TestStep"] == step]["Value"].reset_index(drop=True)

        groups = [data[i:i+5] for i in range(0, len(data), 5) if len(data[i:i+5]) == 5]

        if len(groups) > 1:

            xbars = [g.mean() for g in groups]
            ranges = [g.max() - g.min() for g in groups]

            st.plotly_chart(px.line(xbars, title="Xbar Chart"), use_container_width=True)
            st.plotly_chart(px.line(ranges, title="R Chart"), use_container_width=True)

    # ===============================
    # TREND
    # ===============================
    elif option == "⏱ Trend Chart":

        step = st.selectbox("Select Step", steps)

        if "C" in df.columns:
            subset = df[df["TestStep"] == step]

            fig = px.line(subset, x="C", y="Value", title=step)

            fig.add_hline(y=subset["LSL"].iloc[0], line_dash="dash")
            fig.add_hline(y=subset["USL"].iloc[0], line_dash="dash")

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No time column detected")
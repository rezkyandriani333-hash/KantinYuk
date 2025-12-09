# app.py — Kantingo Financial Dashboard (Streamlit Version)
# Aplikasi mirip contoh Forecast Scenario Planning, tetapi fokus pada Kantingo:
# budgeting, cashflow, category spending, insight AI, dan chatbot.

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from groq import Groq
from dotenv import load_dotenv

# ------------------------------------------------------------
# Load API Key
# ------------------------------------------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("🚨 API Key tidak ditemukan! Tambahkan GROQ_API_KEY ke .env atau Secrets.")
    st.stop()

# Init LLM Client
client = Groq(api_key=GROQ_API_KEY)

# ------------------------------------------------------------
# Streamlit UI Config
# ------------------------------------------------------------
st.set_page_config(page_title="Kantingo AI Dashboard", page_icon="📊", layout="wide")
st.title("📊 Kantingo – Smart Financial Dashboard AI")
st.write("Upload data keuangan dan dapatkan analisis otomatis Kantingo AI.")

# Pilihan Model
selected_model = st.selectbox(
    "🤖 Pilih Model AI",
    ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"],
)

# ------------------------------------------------------------
# Upload File Keuangan
# ------------------------------------------------------------
uploaded_file = st.file_uploader("📂 Upload Dataset Keuangan (Excel)", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # Kolom Minimal
    required_cols = ["Category", "Amount"]
    if not all(col in df.columns for col in required_cols):
        st.error("⚠️ File harus memiliki kolom: Category, Amount")
        st.stop()

    # --------------------------------------------------------
    # Proses Budgeting & Ringkasan
    # --------------------------------------------------------
    st.subheader("📊 Ringkasan Keuangan")

    total_income = df[df["Amount"] > 0]["Amount"].sum()
    total_expense = abs(df[df["Amount"] < 0]["Amount"].sum())
    balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Pemasukan", f"Rp {total_income:,.0f}")
    col2.metric("Pengeluaran", f"Rp {total_expense:,.0f}")
    col3.metric("Saldo", f"Rp {balance:,.0f}")

    # --------------------------------------------------------
    # Category Spending Chart
    # --------------------------------------------------------
    st.subheader("📦 Pengeluaran per Kategori")

    cat_df = df[df["Amount"] < 0].copy()
    cat_df["Expense"] = abs(cat_df["Amount"])
    fig_cat = px.bar(cat_df, x="Category", y="Expense", title="Pengeluaran per Kategori", text_auto=True)
    st.plotly_chart(fig_cat, use_container_width=True)


    # --------------------------------------------------------
    # Buat Forecast (Mirip contoh sebelumnya tapi versi Kantingo)
    # --------------------------------------------------------
    st.subheader("📈 Forecasting versi Kantingo")
    base = abs(cat_df.groupby("Category")["Expense"].sum()).reset_index()
    base.rename(columns={"Expense": "Base Forecast"}, inplace=True)

    base["Optimistic"] = base["Base Forecast"] * np.random.uniform(0.8, 1.0, len(base))
    base["Normal"] = base["Base Forecast"] * np.random.uniform(1.0, 1.2, len(base))
    base["Worst Case"] = base["Base Forecast"] * np.random.uniform(1.2, 1.5, len(base))

    st.dataframe(base)

    fig_forecast = px.bar(
        base,
        x="Category",
        y=["Base Forecast", "Optimistic", "Normal", "Worst Case"],
        barmode="group",
        title="Forecasting Pengeluaran Kantingo",
        text_auto=True,
    )
    st.plotly_chart(fig_forecast, use_container_width=True)


    # --------------------------------------------------------
    # AI Insight (Ringkasan)
    # --------------------------------------------------------
    st.subheader("🤖 Kantingo AI Insight")

    df_preview = base.head(20).to_string(index=False)

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """
                    Kamu adalah Kantingo AI, analis keuangan digital.
                    Berikan insight tentang budgeting, cashflow, kategori terbesar,
                    risiko pengeluaran, dan rekomendasi penghematan.
                    """
                },
                {
                    "role": "user",
                    "content": f"Berikut data forecast pengeluaran:
{df_preview}
Berikan analisis lengkap & rekomendasi."
                }
            ],
            model=selected_model,
        )

        st.write(response.choices[0].message.content)

    except Exception as e:
        st.error(f"AI Error: {e}")


    # --------------------------------------------------------
    # Chatbot Kantingo AI
    # --------------------------------------------------------
    st.subheader("💬 Chat dengan Kantingo AI")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_msg = st.text_input("Tanyakan apa saja tentang keuangan:")

    colA, colB = st.columns([3,1])
    send_btn = colA.button("Kirim")
    reset_btn = colB.button("🔄 Reset")

    if reset_btn:
        st.session_state.chat_history = []
        st.success("Chat telah direset!")

    if send_btn and user_msg:
        try:
            chat_response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Kamu adalah Kantingo AI. Jawab pertanyaan terkait budgeting, cashflow, pengeluaran, serta strategi penghematan."
                    },
                    *st.session_state.chat_history,
                    {"role": "user", "content": user_msg}
                ],
                model=selected_model,
            )

            ai_answer = chat_response.choices[0].message.content
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            st.session_state.chat_history.append({"role": "assistant", "content": ai_answer})

        except Exception as e:
            st.error(f"AI Error: {e}")

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**👤 You:** {msg['content']}")
        else:
            st.markdown(f"**🤖 Kantingo:** {msg['content']}")

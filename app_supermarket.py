import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Controle de Validade de Sucos",
    layout="wide",
    page_icon="🥤"
)

# =========================
# ESTILO PREMIUM
# =========================
st.markdown("""
<style>
.main {
    background-color: #f5f7fa;
}
.stButton>button {
    background-color: #ff6b00;
    color: white;
    border-radius: 10px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =========================
# GOOGLE
# =========================
def conectar_google():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp"],
            scopes=scope
        )
    except:
        creds = Credentials.from_service_account_file(
            "credenciais.json",
            scopes=scope
        )

    return gspread.authorize(creds)


def carregar_dados():
    client = conectar_google()
    sheet = client.open("controle_sucos").sheet1
    return pd.DataFrame(sheet.get_all_records())


def carregar_promotores():
    client = conectar_google()
    sheet = client.open("controle_sucos").worksheet("promotores")
    df = pd.DataFrame(sheet.get_all_records())
    return df["nome"].tolist()

# =========================
# HEADER
# =========================
st.markdown("### 🥤 Controle de Validade de Sucos")
st.caption("Projeto produzido pela Elizabeth Promotoria")

# =========================
# MENU
# =========================
menu = st.sidebar.radio("Menu", ["Registro", "Dashboard"])

# =========================
# REGISTRO
# =========================
if menu == "Registro":

    st.header("📋 Registro")

    promotores = carregar_promotores()

    col1, col2 = st.columns(2)

    with col1:
        visita_por = st.selectbox("👤 Visitado por", promotores)
        data_producao = st.date_input("📅 Data", datetime.today())
        loja = st.selectbox("🏪 Loja", ["Loja A", "Loja B"])

    with col2:
        produto = st.selectbox("🍊 Produto", ["Laranja", "Morango"])
        tamanho = st.selectbox("📦 Tamanho", ["500ml", "1L"])

    st.markdown("### ⏳ Validade")

    col1, col2, col3 = st.columns(3)

    v7 = col1.number_input("Até 7 dias", min_value=0)
    v15 = col2.number_input("Até 15 dias", min_value=0)
    v30 = col3.number_input("30+ dias", min_value=0)

    quantidade = v7 + v15 + v30

    st.metric("📦 Estoque Total", quantidade)

    if st.button("Salvar", use_container_width=True):

        client = conectar_google()
        sheet = client.open("controle_sucos").sheet1

        sheet.append_row([
            visita_por,
            str(data_producao),
            loja,
            produto,
            tamanho,
            quantidade,
            v7,
            v15,
            v30
        ])

        st.success("Salvo com sucesso!")

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    # LOGIN
    usuarios = {"admin": "123"}

    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if usuarios.get(user) == senha:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Erro login")

        st.stop()

    df = carregar_dados()

    if df.empty:
        st.warning("Sem dados")
        st.stop()

    # =========================
    # TRATAMENTO
    # =========================
    df["data"] = pd.to_datetime(df["data"])

    # =========================
    # FILTROS
    # =========================
    st.sidebar.markdown("### Filtros")

    promotor = st.sidebar.multiselect(
        "Promotor",
        df["visita_por"].unique(),
        default=df["visita_por"].unique()
    )

    data_inicio = st.sidebar.date_input("Data início", df["data"].min())
    data_fim = st.sidebar.date_input("Data fim", df["data"].max())

    df = df[
        (df["visita_por"].isin(promotor)) &
        (df["data"] >= pd.to_datetime(data_inicio)) &
        (df["data"] <= pd.to_datetime(data_fim))
    ]

    # =========================
    # KPIs
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("📦 Estoque", int(df["quantidade"].sum()))
    col2.metric("⚠️ Vencendo", int(df["v7"].sum()))
    col3.metric("🏪 Lojas", df["loja"].nunique())

    st.markdown("---")

    # =========================
    # GRÁFICOS
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Estoque por Loja")
        st.bar_chart(df.groupby("loja")["quantidade"].sum())

    with col2:
        st.subheader("Validade")
        st.bar_chart(df[["v7", "v15", "v30"]].sum())

    st.markdown("---")

    st.subheader("Evolução")
    st.line_chart(df.groupby("data")["quantidade"].sum())

    st.markdown("---")

    # =========================
    # RANKING
    # =========================
    st.subheader("🏆 Ranking de Promotores")

    ranking = (
        df.groupby("visita_por")["quantidade"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    ranking.columns = ["Promotor", "Volume"]

    st.dataframe(ranking, use_container_width=True)
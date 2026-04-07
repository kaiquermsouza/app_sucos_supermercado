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
# ESTILO
# =========================
st.markdown("""
<style>
.main {
    background-color: #f5f7fa;
}
</style>
""", unsafe_allow_html=True)

# =========================
# GOOGLE SHEETS (SEGURO)
# =========================
def conectar_google():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        # 🔐 PRODUÇÃO (Streamlit Cloud)
        creds = Credentials.from_service_account_info(
            st.secrets["gcp"],
            scopes=scope
        )
    except Exception:
        # 💻 LOCAL (seu PC)
        creds = Credentials.from_service_account_file(
            "credenciais.json",
            scopes=scope
        )

    client = gspread.authorize(creds)
    return client.open("controle_sucos").sheet1


def carregar_dados():
    sheet = conectar_google()
    dados = sheet.get_all_records()
    return pd.DataFrame(dados)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🥤 Controle de Sucos")
menu = st.sidebar.radio("Menu", ["Registro", "Dashboard"])

# =========================
# REGISTRO
# =========================
if menu == "Registro":
    
    st.title("📋 Registro de Estoque")

    col1, col2 = st.columns(2)

    with col1:
        data_producao = st.date_input("📅 Data", datetime.today())
        loja = st.selectbox("🏪 Loja", ["Loja A", "Loja B"])
    
    with col2:
        produto = st.selectbox("🍊 Produto", ["Laranja", "Morango"])
        tamanho = st.selectbox("📦 Tamanho", ["500ml", "1L"])

    st.markdown("### ⏳ Validade dos Produtos")

    col1, col2, col3 = st.columns(3)

    with col1:
        v7 = st.number_input("Até 7 dias", min_value=0)

    with col2:
        v15 = st.number_input("Até 15 dias", min_value=0)

    with col3:
        v30 = st.number_input("30+ dias", min_value=0)

    quantidade = v7 + v15 + v30

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("📦 Estoque Total", quantidade)

    with col2:
        if v7 > 0:
            st.error("⚠️ Produtos próximos do vencimento!")
        else:
            st.success("✅ Estoque saudável")

    if st.button("💾 Salvar Registro", use_container_width=True):
        try:
            sheet = conectar_google()

            nova_linha = [
                str(data_producao),
                loja,
                produto,
                tamanho,
                quantidade,
                v7,
                v15,
                v30
            ]

            sheet.append_row(nova_linha)

            st.success("✅ Registro salvo com sucesso!")

        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    usuarios = {
        "admin": "123",
        "gerente": "456"
    }

    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🔐 Acesso ao Dashboard")

        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if user in usuarios and usuarios[user] == senha:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

        st.stop()

    st.title("📊 Dashboard Gerencial")

    try:
        df = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

    if df.empty:
        st.warning("Sem dados ainda.")
        st.stop()

    # KPIs
    total_estoque = df["quantidade"].sum()
    total_v7 = df["v7"].sum()
    total_lojas = df["loja"].nunique()

    col1, col2, col3 = st.columns(3)

    col1.metric("📦 Estoque Total", total_estoque)
    col2.metric("⚠️ Vencendo (7 dias)", total_v7)
    col3.metric("🏪 Lojas Ativas", total_lojas)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Estoque por Loja")
        st.bar_chart(df.groupby("loja")["quantidade"].sum())

    with col2:
        st.subheader("⏳ Distribuição de Validade")
        st.bar_chart(df[["v7", "v15", "v30"]].sum())

    st.markdown("---")

    st.subheader("📈 Evolução de Registros")

    df["data"] = pd.to_datetime(df["data"])
    evolucao = df.groupby("data")["quantidade"].sum()

    st.line_chart(evolucao)
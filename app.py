"""
Plataforma Financeira Integrada (Tríade: Macro + Mercado + Balanços)
Aplicação Corporativa de Business Intelligence desenvolvida em Streamlit
"""

import streamlit as st
import pandas as pd
from src.database import carregar_dados_completos

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Plataforma Financeira Integrada | Tríade",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. CARREGAMENTO RESILIENTE DOS DADOS
# -----------------------------------------------------------------------------
try:
    dados, fontes = carregar_dados_completos()
    df_macro = dados["macro_bacen"]
    df_mercado = dados["mercado_b3"]
    df_balancos = dados["balancos_cvm"]
    df_triade = dados["triade_consolidada"]
    fonte_ativa = fontes["triade_consolidada"]
except Exception as e:
    st.error(f"Erro crítico no carregamento da base de dados: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. GESTÃO DE ESTADO (st.session_state) E FILTROS NA SIDEBAR
# -----------------------------------------------------------------------------
# Valores padrão dos filtros
OPCAO_TODOS = "Todos"
ANOS_DISPONIVEIS = sorted(df_triade["ano"].unique().tolist())
SETORES_DISPONIVEIS = sorted(df_triade["setor"].unique().tolist())
TICKERS_DISPONIVEIS = sorted(df_triade["ticker"].unique().tolist())

if "filtro_ano" not in st.session_state:
    st.session_state.filtro_ano = OPCAO_TODOS
if "filtro_setor" not in st.session_state:
    st.session_state.filtro_setor = OPCAO_TODOS
if "filtro_ticker" not in st.session_state:
    st.session_state.filtro_ticker = OPCAO_TODOS


def resetar_filtros():
    """Função callback para restaurar o estado padrão dos filtros."""
    st.session_state.filtro_ano = OPCAO_TODOS
    st.session_state.filtro_setor = OPCAO_TODOS
    st.session_state.filtro_ticker = OPCAO_TODOS


with st.sidebar:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/2784/2784403.png",
        width=70
    )
    st.title("Painel de Controle")
    st.markdown("Filtros dinâmicos e parâmetros analíticos")

    # Filtro 1: Ano do Exercício Fiscal
    ano_selecionado = st.selectbox(
        "Exercício Fiscal (Ano):",
        options=[OPCAO_TODOS] + ANOS_DISPONIVEIS,
        key="filtro_ano"
    )

    # Filtro 2: Setor Econômico
    setor_selecionado = st.selectbox(
        "Setor Econômico:",
        options=[OPCAO_TODOS] + SETORES_DISPONIVEIS,
        key="filtro_setor"
    )

    # Filtro 3: Ticker / Ativo
    # Filtro reativo: restringe tickers ao setor selecionado se aplicável
    if setor_selecionado != OPCAO_TODOS:
        tickers_filtrados = sorted(
            df_triade[df_triade["setor"] == setor_selecionado]["ticker"].unique().tolist()
        )
    else:
        tickers_filtrados = TICKERS_DISPONIVEIS

    ticker_selecionado = st.selectbox(
        "Ativo / Companhia:",
        options=[OPCAO_TODOS] + tickers_filtrados,
        key="filtro_ticker"
    )

    st.markdown("---")
    st.button("🔄 Redefinir Filtros", on_click=resetar_filtros, use_container_width=True)

    st.markdown("---")
    # Indicador de Governança de Dados e Conectividade
    st.caption("📡 **Camada de Dados Ativa:**")
    if "Supabase" in fonte_ativa:
        st.success(f"Conectado: {fonte_ativa}")
    else:
        st.warning(f"Operando em: {fonte_ativa}")

# -----------------------------------------------------------------------------
# 4. APLICAÇÃO DOS FILTROS NAS BASES DE DADOS
# -----------------------------------------------------------------------------
df_triade_filtrado = df_triade.copy()
df_mercado_filtrado = df_mercado.copy()
df_balancos_filtrado = df_balancos.copy()

if st.session_state.filtro_ano != OPCAO_TODOS:
    df_triade_filtrado = df_triade_filtrado[df_triade_filtrado["ano"] == st.session_state.filtro_ano]
    df_balancos_filtrado = df_balancos_filtrado[df_balancos_filtrado["ano"] == st.session_state.filtro_ano]
    df_mercado_filtrado = df_mercado_filtrado[
        pd.to_datetime(df_mercado_filtrado["data"]).dt.year == st.session_state.filtro_ano
    ]

if st.session_state.filtro_setor != OPCAO_TODOS:
    df_triade_filtrado = df_triade_filtrado[df_triade_filtrado["setor"] == st.session_state.filtro_setor]
    df_balancos_filtrado = df_balancos_filtrado[df_balancos_filtrado["setor"] == st.session_state.filtro_setor]
    df_mercado_filtrado = df_mercado_filtrado[df_mercado_filtrado["setor"] == st.session_state.filtro_setor]

if st.session_state.filtro_ticker != OPCAO_TODOS:
    df_triade_filtrado = df_triade_filtrado[df_triade_filtrado["ticker"] == st.session_state.filtro_ticker]
    df_balancos_filtrado = df_balancos_filtrado[df_balancos_filtrado["ticker"] == st.session_state.filtro_ticker]
    df_mercado_filtrado = df_mercado_filtrado[df_mercado_filtrado["ticker"] == st.session_state.filtro_ticker]

# -----------------------------------------------------------------------------
# 5. CABEÇALHO EXECUTIVO E CONTEXTUALIZAÇÃO
# -----------------------------------------------------------------------------
st.title("🏛️ Plataforma Financeira Integrada")
st.subheader("Tríade Estratégica: Cenário Macroeconômico + Mercado de Capitais + Demonstrações Contábeis")
st.markdown(
    """
    Esta plataforma correlaciona a política monetária nacional (**BACEN/SGS**), 
    o comportamento dos preços e risco em bolsa (**B3**) e os balanços auditados das companhias (**CVM**).
    Utilize os seletores laterais para avaliar a sensibilidade e a resiliência corporativa entre 2021 e 2023.
    """
)
st.markdown("---")

# -----------------------------------------------------------------------------
# 6. ESPAÇO RESERVADO PARA OS KPIS ESTRATÉGICOS (CARD 07)
# -----------------------------------------------------------------------------
st.markdown("### 📌 Indicadores-Chave de Desempenho (KPIs)")
placeholder_kpis = st.container()
with placeholder_kpis:
    st.info("Painel de KPIs Estratégicos será conectado na próxima etapa (Card 07).")

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. NAVEGAÇÃO ESTRUTURADA EM ABAS (st.tabs)
# -----------------------------------------------------------------------------
tab_triade, tab_macro, tab_b3, tab_cvm, tab_dados = st.tabs([
    "🌐 Visão Integrada (Tríade)",
    "📊 Macroeconomia (BACEN)",
    "📈 Mercado de Ações (B3)",
    "📑 Balanços e Contabilidade (CVM)",
    "💾 Base de Dados e Exportação"
])

with tab_triade:
    st.markdown("#### 🔄 Cruzamento Multivariado: Macro vs. Mercado vs. Balanços")
    st.write(
        f"Registros ativos após aplicação dos filtros: **{len(df_triade_filtrado)} observações**."
    )
    st.caption("Os gráficos cruzados em Plotly Express serão renderizados aqui (Card 08).")

with tab_macro:
    st.markdown("#### 🏦 Panorama Macroeconômico e Ciclo de Juros (2019 - 2023)")
    st.dataframe(df_macro.head(10), use_container_width=True)

with tab_b3:
    st.markdown("#### 📉 Performance Histórica e Risco dos Ativos (B3)")
    st.dataframe(df_mercado_filtrado.head(10), use_container_width=True)

with tab_cvm:
    st.markdown("#### 🏢 Saúde Econômico-Financeira e Margens Corporativas (CVM)")
    st.dataframe(df_balancos_filtrado.head(10), use_container_width=True)

with tab_dados:
    st.markdown("#### 📥 Repositório de Dados Consolidados da Tríade")
    st.dataframe(df_triade_filtrado, use_container_width=True)
    
    # Recurso obrigatório de exportação (Item 4.5 do edital)
    csv_bytes = df_triade_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar Dados Filtrados (CSV)",
        data=csv_bytes,
        file_name="triade_financeira_filtrada.csv",
        mime="text/csv",
        use_container_width=True
    )
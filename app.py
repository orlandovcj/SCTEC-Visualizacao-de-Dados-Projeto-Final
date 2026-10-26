"""
Plataforma Financeira Integrada (Tríade: Macro + Mercado + Balanços)
Aluno: Orlando Vieira de Castro Junior
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.database import carregar_dados_completos

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Plataforma Financeira Integrada | Tríade",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. DESIGN SYSTEM: CSS CORPORATIVO COM CARDS ELEVADOS (ARCHITECTUI)
# -----------------------------------------------------------------------------
def aplicar_estilo_architectui():
    st.markdown(
        """
        <style>
        /* Fundo geral em cinza suave executivo */
        .stApp {
            background-color: #f8f9fa;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Sidebar limpa */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e9ecef;
        }

        /* 1. CARDS DE KPIS (st.metric) */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 16px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        }

        div[data-testid="stMetric"] label {
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #64748b !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 1.80rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
        }

        /* 2. CARDS DE GRÁFICOS (st.container com border=True) */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            background-color: #ffffff;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            padding: 20px !important;
            margin-bottom: 16px;
        }

        /* Títulos internos dos Cards */
        .card-header-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 2px;
        }

        .card-header-subtitle {
            font-size: 0.85rem;
            color: #64748b;
            margin-bottom: 14px;
        }

        /* Abas Corporativas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: 10px 18px;
            font-weight: 600;
            color: #64748b;
            background-color: transparent;
        }

        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #2563eb !important;
            border-bottom: 3px solid #2563eb !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

aplicar_estilo_architectui()

def formatar_figura_card(fig):
    """Garante fundo transparente e margens harmônicas dentro do contêiner do card."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", family="Segoe UI, sans-serif"),
        margin=dict(t=35, b=30, l=30, r=30)
    )
    return fig

# -----------------------------------------------------------------------------
# 3. CARREGAMENTO RESILIENTE DOS DADOS
# -----------------------------------------------------------------------------
try:
    dados, fontes = carregar_dados_completos()
    df_macro = dados["macro_bacen"]
    df_mercado = dados["mercado_b3"]
    df_balancos = dados["balancos_cvm"]
    df_triade = dados["triade_consolidada"]
    fonte_ativa = fontes["triade_consolidada"]
except Exception as erro:
    st.error(f"Erro crítico no carregamento da base de dados: {erro}")
    st.stop()

# Harmonização temporal
df_macro["referencia_mensal"] = pd.to_datetime(df_macro["referencia_mensal"])
df_mercado["data"] = pd.to_datetime(df_mercado["data"])

# -----------------------------------------------------------------------------
# 4. GESTÃO DE ESTADO (st.session_state) E SIDEBAR COM SELEÇÃO MÚLTIPLA
# -----------------------------------------------------------------------------
OPCAO_TODOS = "Todos"
ANOS_DISPONIVEIS = sorted(df_triade["ano"].unique().tolist())
SETORES_DISPONIVEIS = sorted(df_triade["setor"].unique().tolist())
TICKERS_DISPONIVEIS = sorted(df_triade["ticker"].unique().tolist())

if "filtro_ano" not in st.session_state:
    st.session_state.filtro_ano = []
if "filtro_setor" not in st.session_state:
    st.session_state.filtro_setor = []
if "filtro_ticker" not in st.session_state:
    st.session_state.filtro_ticker = []


def resetar_filtros():
    """Restaura todos os seletores para o estado consolidado amplo."""
    st.session_state.filtro_ano = []
    st.session_state.filtro_setor = []
    st.session_state.filtro_ticker = []


with st.sidebar:
    st.title("🎛️ Painel de Controle")
    st.markdown("Filtros dinâmicos múltiplos da Tríade")

    anos_selecionados = st.multiselect(
        "Exercício Fiscal (Ano):",
        options=ANOS_DISPONIVEIS,
        default=st.session_state.filtro_ano,
        key="filtro_ano",
        placeholder="Todos os anos"
    )

    setores_selecionados = st.multiselect(
        "Setores Econômicos:",
        options=SETORES_DISPONIVEIS,
        default=st.session_state.filtro_setor,
        key="filtro_setor",
        placeholder="Todos os setores"
    )

    if st.session_state.filtro_setor:
        tickers_disponiveis_reativos = sorted(
            df_triade[df_triade["setor"].isin(st.session_state.filtro_setor)]["ticker"].unique().tolist()
        )
    else:
        tickers_disponiveis_reativos = TICKERS_DISPONIVEIS

    # Higienização de integridade relacional
    st.session_state.filtro_ticker = [
        t for t in st.session_state.filtro_ticker if t in tickers_disponiveis_reativos
    ]

    tickers_selecionados = st.multiselect(
        "Ativos / Companhias:",
        options=tickers_disponiveis_reativos,
        default=st.session_state.filtro_ticker,
        key="filtro_ticker",
        placeholder="Todos os ativos"
    )

    st.markdown("---")
    st.button("🔄 Redefinir Filtros", on_click=resetar_filtros, use_container_width=True)
    
    st.markdown("---")
    st.caption("📡 **Camada de Dados Ativa:**")
    if "Supabase" in fonte_ativa:
        st.success(f"Conectado: {fonte_ativa}")
    else:
        st.warning(f"Operando em: {fonte_ativa}")

# -----------------------------------------------------------------------------
# 5. APLICAÇÃO DOS FILTROS NAS BASES (USO SEGURO DE .isin())
# -----------------------------------------------------------------------------
df_triade_f = df_triade.copy()
df_mercado_f = df_mercado.copy()
df_balancos_f = df_balancos.copy()
df_macro_f = df_macro.copy()

if st.session_state.filtro_ano:
    df_triade_f = df_triade_f[df_triade_f["ano"].isin(st.session_state.filtro_ano)]
    df_balancos_f = df_balancos_f[df_balancos_f["ano"].isin(st.session_state.filtro_ano)]
    df_mercado_f = df_mercado_f[df_mercado_f["data"].dt.year.isin(st.session_state.filtro_ano)]
    df_macro_f = df_macro_f[df_macro_f["referencia_mensal"].dt.year.isin(st.session_state.filtro_ano)]

if st.session_state.filtro_setor:
    df_triade_f = df_triade_f[df_triade_f["setor"].isin(st.session_state.filtro_setor)]
    df_balancos_f = df_balancos_f[df_balancos_f["setor"].isin(st.session_state.filtro_setor)]
    df_mercado_f = df_mercado_f[df_mercado_f["setor"].isin(st.session_state.filtro_setor)]

if st.session_state.filtro_ticker:
    df_triade_f = df_triade_f[df_triade_f["ticker"].isin(st.session_state.filtro_ticker)]
    df_balancos_f = df_balancos_f[df_balancos_f["ticker"].isin(st.session_state.filtro_ticker)]
    df_mercado_f = df_mercado_f[df_mercado_f["ticker"].isin(st.session_state.filtro_ticker)]

# -----------------------------------------------------------------------------
# 6. CABEÇALHO EXECUTIVO
# -----------------------------------------------------------------------------
st.title("🏛️ Plataforma Financeira Integrada")
st.markdown(
    """
    Solução analítica corporativa estruturada em conformidade com as quatro linhas temáticas do edital.
    Cada aba apresenta seus **KPIs estratégicos dedicados**, visualizações analíticas em **cards padronizados** 
    e evidências empíricas voltadas à tomada de decisão de investimento e avaliação de risco corporativo.
    """
)
st.markdown("---")

# -----------------------------------------------------------------------------
# 7. ESTRUTURAÇÃO MODULAR EM ABAS
# -----------------------------------------------------------------------------
tab_l4, tab_l2, tab_l1, tab_l3, tab_exp = st.tabs([
    "🌐 Linha 4: Tríade Integrada",
    "📈 Linha 2: Mercado de Ações (B3)",
    "🏢 Linha 1: Balanços Contábeis (CVM)",
    "🏦 Linha 3: Macroeconomia (BACEN)",
    "💾 Base de Dados & Exportação"
])

# =============================================================================
# ABA 1: LINHA 4 - PLATAFORMA FINANCEIRA INTEGRADA (TRÍADE)
# =============================================================================
with tab_l4:
    st.subheader("🌐 Linha 4: Plataforma Financeira Integrada (Tríade: Macro + Mercado + Balanços)")
    st.caption("Visão multivariada integrando conjuntura econômica (BACEN), precificação em bolsa (B3) e balanços (CVM).")

    # 1. GRADE OFICIAL DE KPIS ESTRATÉGICOS (LINHA 4)
    if len(st.session_state.filtro_ano) == 1:
        ano_ref_kpi = int(st.session_state.filtro_ano[0])
    else:
        ano_ref_kpi = 2023        
    df_macro_ano_atual = df_macro[df_macro["referencia_mensal"].dt.year == ano_ref_kpi].sort_values("referencia_mensal")
    df_macro_ano_ant = df_macro[df_macro["referencia_mensal"].dt.year == (ano_ref_kpi - 1)].sort_values("referencia_mensal")

    selic_atual_val = df_macro_ano_atual["selic_meta"].iloc[-1] if not df_macro_ano_atual.empty else 11.75
    ipca_atual_val = df_macro_ano_atual["ipca_12m"].iloc[-1] if not df_macro_ano_atual.empty else 4.62

    if not df_macro_ano_ant.empty:
        delta_selic_kpi = selic_atual_val - df_macro_ano_ant["selic_meta"].iloc[-1]
        delta_ipca_kpi = ipca_atual_val - df_macro_ano_ant["ipca_12m"].iloc[-1]
        rotulo_macro_kpi = f"vs. {ano_ref_kpi - 1}"
    else:
        delta_selic_kpi = delta_ipca_kpi = None
        rotulo_macro_kpi = "Marco Base (2019)"

    receita_total_bi = df_balancos_f["receita_liquida"].sum() / 1e9
    lucro_total_bi = df_balancos_f["lucro_liquido"].sum() / 1e9

    delta_rec_kpi = None
    delta_lucro_kpi = None
    rotulo_contabil_kpi = "Consolidado Triênio"

    if len(st.session_state.filtro_ano) == 1:
        ano_sel_int = int(st.session_state.filtro_ano[0])
        if ano_sel_int > 2021:
            ano_ant_int = ano_sel_int - 1
            df_ant_kpi = df_balancos[df_balancos["ano"] == ano_ant_int].copy()
            if st.session_state.filtro_setor:
                df_ant_kpi = df_ant_kpi[df_ant_kpi["setor"].isin(st.session_state.filtro_setor)]
            if st.session_state.filtro_ticker:
                df_ant_kpi = df_ant_kpi[df_ant_kpi["ticker"].isin(st.session_state.filtro_ticker)]

            rec_ant_bi = df_ant_kpi["receita_liquida"].sum() / 1e9
            lucro_ant_bi = df_ant_kpi["lucro_liquido"].sum() / 1e9

            if rec_ant_bi > 0:
                delta_rec_kpi = ((receita_total_bi - rec_ant_bi) / rec_ant_bi) * 100
            if lucro_ant_bi != 0:
                delta_lucro_kpi = ((lucro_total_bi - lucro_ant_bi) / abs(lucro_ant_bi)) * 100
            rotulo_contabil_kpi = f"vs. {ano_ant_int}"
        else:
            rotulo_contabil_kpi = "Início da Série (2021)"
    elif len(st.session_state.filtro_ano) > 1:
        rotulo_contabil_kpi = "Consolidado Seleção"

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric(
            label="Taxa Selic Meta Atual",
            value=f"{selic_atual_val:.2f}% a.a.",
            delta=f"{delta_selic_kpi:+.2f} p.p. {rotulo_macro_kpi}" if delta_selic_kpi is not None else rotulo_macro_kpi,
            help="Taxa básica de juros definida pelo COPOM/BACEN ao final do período."
        )

    with k2:
        st.metric(
            label="Inflação IPCA 12M",
            value=f"{ipca_atual_val:.2f}% a.a.",
            delta=f"{delta_ipca_kpi:+.2f} p.p. {rotulo_macro_kpi}" if delta_ipca_kpi is not None else rotulo_macro_kpi,
            delta_color="inverse",
            help="Índice Nacional de Preços ao Consumidor Amplo acumulado em 12 meses."
        )

    with k3:
        st.metric(
            label="Receita Consolidada da Carteira",
            value=f"R$ {receita_total_bi:,.1f} Bi",
            delta=f"{delta_rec_kpi:+.1f}% {rotulo_contabil_kpi}" if delta_rec_kpi is not None else rotulo_contabil_kpi,
            help="Soma do faturamento operacional líquido das companhias sob os filtros selecionados."
        )

    with k4:
        st.metric(
            label="Lucro Líquido da Carteira",
            value=f"R$ {lucro_total_bi:,.1f} Bi",
            delta=f"{delta_lucro_kpi:+.1f}% {rotulo_contabil_kpi}" if delta_lucro_kpi is not None else rotulo_contabil_kpi,
            help="Resultado líquido final gerado aos acionistas após tributos e despesas financeiras."
        )

    st.markdown("---")

    # 2. GRADE OFICIAL DE VISUALIZAÇÕES EM CARDS (LINHA 4)
    # Card 1: Gráfico Multieixo Macro-Cambial
    with st.container(border=True):
        st.markdown('<div class="card-header-title">1. Gráfico Multieixo Macro-Cambial</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-header-subtitle">Trajetória da Selic, IPCA e Dólar PTAX com eixos duplos integrados</div>', unsafe_allow_html=True)

        df_macro_triade_plot = df_macro.copy() if not st.session_state.filtro_ano else df_macro_f.copy()

        fig_multieixo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_multieixo.add_trace(
            go.Scatter(
                x=df_macro_triade_plot["referencia_mensal"],
                y=df_macro_triade_plot["selic_meta"],
                name="Selic Meta (% a.a.)",
                line=dict(color="#1f77b4", width=3)
            ),
            secondary_y=False
        )
        fig_multieixo.add_trace(
            go.Scatter(
                x=df_macro_triade_plot["referencia_mensal"],
                y=df_macro_triade_plot["ipca_12m"],
                name="IPCA 12M (% a.a.)",
                line=dict(color="#d62728", width=2, dash="dot")
            ),
            secondary_y=False
        )
        fig_multieixo.add_trace(
            go.Scatter(
                x=df_macro_triade_plot["referencia_mensal"],
                y=df_macro_triade_plot["dolar_ptax"],
                name="Dólar PTAX (R$)",
                line=dict(color="#ff7f0e", width=2, dash="dash")
            ),
            secondary_y=True
        )

        fig_multieixo.update_layout(
            legend=dict(orientation="h", y=-0.18),
            hovermode="x unified"
        )
        fig_multieixo.update_yaxes(title_text="Taxas (% a.a.)", secondary_y=False)
        fig_multieixo.update_yaxes(title_text="Câmbio Comercial (R$)", secondary_y=True)
        
        fig_multieixo = formatar_figura_card(fig_multieixo)
        st.plotly_chart(fig_multieixo, use_container_width=True)

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        # Card 2: Comparativo Base 100 na B3
        with st.container(border=True):
            st.markdown('<div class="card-header-title">2. Retorno Relativo Base 100 (B3)</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Evolução normalizada das ações (P₀ = 100 no início do período)</div>', unsafe_allow_html=True)

            df_base100_t = df_mercado_f.copy().sort_values(["ticker", "data"])
            if not df_base100_t.empty:
                df_base100_t["base_100_dinamica"] = df_base100_t.groupby("ticker")["preco_ajustado"].transform(
                    lambda x: (x / x.iloc[0]) * 100
                )

                fig_base100_triade = px.line(
                    df_base100_t,
                    x="data",
                    y="base_100_dinamica",
                    color="ticker",
                    labels={"data": "Data", "base_100_dinamica": "Base 100", "ticker": "Ativo"}
                )
                fig_base100_triade.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Neutro (100)")
                fig_base100_triade.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.2))
                
                fig_base100_triade = formatar_figura_card(fig_base100_triade)
                st.plotly_chart(fig_base100_triade, use_container_width=True)
            else:
                st.info("Nenhum dado disponível para os filtros selecionados.")

    with col_t2:
        # Card 3: Balanços CVM - Lucro Líquido vs ROE
        with st.container(border=True):
            st.markdown('<div class="card-header-title">3. Balanços CVM: Lucro Líquido vs. ROE</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Lucro consolidado auditado (R$ Bi) e taxa de retorno sobre o PL</div>', unsafe_allow_html=True)

            df_bal_t = df_balancos_f.copy()
            df_bal_t["lucro_bi"] = df_bal_t["lucro_liquido"] / 1e9

            fig_barras_cvm = make_subplots(specs=[[{"secondary_y": True}]])
            fig_barras_cvm.add_trace(
                go.Bar(
                    x=df_bal_t["ticker"],
                    y=df_bal_t["lucro_bi"],
                    name="Lucro Líquido (R$ Bi)",
                    marker_color="#2ecc71"
                ),
                secondary_y=False
            )
            fig_barras_cvm.add_trace(
                go.Scatter(
                    x=df_bal_t["ticker"],
                    y=df_bal_t["roe"],
                    name="ROE (%)",
                    mode="lines+markers",
                    line=dict(color="#8e44ad", width=2),
                    marker=dict(size=7)
                ),
                secondary_y=True
            )
            fig_barras_cvm.add_hline(y=13.75, line_dash="dot", line_color="orange", secondary_y=True, annotation_text="Benchmark Selic Final")
            fig_barras_cvm.update_layout(legend=dict(orientation="h", y=-0.2))
            fig_barras_cvm.update_yaxes(title_text="Lucro Líquido (R$ Bi)", secondary_y=False)
            fig_barras_cvm.update_yaxes(title_text="ROE (%)", secondary_y=True)
            
            fig_barras_cvm = formatar_figura_card(fig_barras_cvm)
            st.plotly_chart(fig_barras_cvm, use_container_width=True)

    col_t3, col_t4 = st.columns(2)

    with col_t3:
        # Card 4: Retorno Setorial na B3 vs Selic Média Anual
        with st.container(border=True):
            st.markdown('<div class="card-header-title">4. Retorno Setorial B3 vs. Selic Média Anual</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Performance das ações agrupadas por setor frente à taxa média básica</div>', unsafe_allow_html=True)

            df_triade_plot_bar = df_triade.copy()
            if st.session_state.filtro_setor:
                df_triade_plot_bar = df_triade_plot_bar[df_triade_plot_bar["setor"].isin(st.session_state.filtro_setor)]
            
            df_setor_ano = df_triade_plot_bar.groupby(["ano", "setor"]).agg(
                retorno_medio_b3=("retorno_anual_b3", "mean"),
                selic_media=("selic_media_ano", "first")
            ).reset_index()

            df_selic_linha = df_triade.groupby("ano")["selic_media_ano"].first().reset_index()

            fig_barras_cruzadas = make_subplots(specs=[[{"secondary_y": True}]])
            paleta_setores = px.colors.qualitative.Safe

            for i, setor_nome in enumerate(df_setor_ano["setor"].unique()):
                df_subset = df_setor_ano[df_setor_ano["setor"] == setor_nome]
                fig_barras_cruzadas.add_trace(
                    go.Bar(
                        x=df_subset["ano"].astype(str),
                        y=df_subset["retorno_medio_b3"],
                        name=setor_nome,
                        text=df_subset["retorno_medio_b3"].apply(lambda v: f"{v:+.1f}%"),
                        textposition="outside",
                        marker_color=paleta_setores[i % len(paleta_setores)]
                    ),
                    secondary_y=False
                )

            fig_barras_cruzadas.add_trace(
                go.Scatter(
                    x=df_selic_linha["ano"].astype(str),
                    y=df_selic_linha["selic_media_ano"],
                    name="Taxa Selic Média",
                    mode="lines+markers+text",
                    line=dict(color="#FF8C00", width=3),
                    marker=dict(size=9, color="#FF8C00"),
                    text=df_selic_linha["selic_media_ano"].apply(lambda v: f"{v:.1f}%"),
                    textposition="top center",
                    textfont=dict(color="#FF8C00", size=11)
                ),
                secondary_y=True
            )

            fig_barras_cruzadas.add_hline(y=0, line_dash="solid", line_color="gray", secondary_y=False)
            fig_barras_cruzadas.update_layout(
                barmode="group",
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
                hovermode="x unified"
            )
            fig_barras_cruzadas.update_yaxes(title_text="Retorno Setorial B3 (%)", secondary_y=False)
            fig_barras_cruzadas.update_yaxes(title_text="Taxa Selic Média (%)", secondary_y=True, showgrid=False)
            fig_barras_cruzadas.update_xaxes(type="category", title_text="Exercício Fiscal")

            fig_barras_cruzadas = formatar_figura_card(fig_barras_cruzadas)
            st.plotly_chart(fig_barras_cruzadas, use_container_width=True)

    with col_t4:
        # Card 5: Dispersão Fundamentalista Tríade
        with st.container(border=True):
            st.markdown('<div class="card-header-title">5. Dispersão: Margem EBIT vs. Retorno B3</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Eficiência operacional e valorização de mercado [Tamanho = Receita Líquida]</div>', unsafe_allow_html=True)

            fig_disp_triade = px.scatter(
                df_triade_f,
                x="margem_ebit",
                y="retorno_anual_b3",
                color="setor",
                size="receita_liquida",
                hover_name="ticker",
                hover_data=["ano", "roe", "divida_liquida"],
                labels={"margem_ebit": "Margem EBIT Operacional (%)", "retorno_anual_b3": "Retorno na B3 (%)"}
            )
            fig_disp_triade.add_hline(y=0, line_dash="solid", line_color="gray")
            fig_disp_triade.add_vline(x=0, line_dash="dash", line_color="gray")
            
            fig_disp_triade = formatar_figura_card(fig_disp_triade)
            st.plotly_chart(fig_disp_triade, use_container_width=True)

    st.info(
        """
        **Síntese Executiva da Tríade Integrada (Resolução das Perguntas de Negócio):**
        * **Impacto do Aperto Monetário (Pergunta 1):** A elevação da Selic de 2,00% para 13,75% ampliou significativamente o custo da dívida das companhias alavancadas, penalizando as margens líquidas e o resultado final principalmente em 2022 e 2023.
        * **Sensibilidade Setorial (Pergunta 2):** Setores de Consumo Cíclico sofreram compressão de múltiplos em bolsa, enquanto os setores Financeiro e de Energia Elétrica mantiveram estabilidade operacional e ROE superior ao custo de oportunidade da renda fixa.
        * **Proteção Cambial de Commodities (Pergunta 3):** Produtoras de commodities (Petróleo e Materiais Básicos) exibiram descorrelação positiva frente ao ciclo doméstico, beneficiando-se da receita dolarizada nos períodos de desvalorização do Real frente ao Dólar PTAX.
        * **Resiliência Integrada (Pergunta 4):** Empresas que combinaram margens EBIT saudáveis, baixa alavancagem financeira líquida e geração de caixa previsível sustentaram retornos positivos em bolsa mesmo durante o pico do aperto monetário.
        """
    )
    
    # =============================================================================
# ABA 2: LINHA 2 - ANÁLISE TÉCNICA E PERFORMANCE DE MERCADO DE AÇÕES (B3)
# =============================================================================
with tab_l2:
    st.subheader("📈 Linha 2: Análise Técnica e Performance de Mercado de Ações (B3)")
    st.caption("Métricas quantitativas de retorno, volatilidade realizada, risco de cauda e médias móveis.")

    # -------------------------------------------------------------------------
    # 1. PROCESSAMENTO ANALÍTICO DOS ATIVOS NO RECORTE ATIVO
    # -------------------------------------------------------------------------
    if df_mercado_f.empty:
        st.warning("Nenhum registro de negociação encontrado para os filtros selecionados.")
    else:
        # Cálculo de retorno acumulado e volatilidade média por ativo no período filtrado
        resumo_ativos = []
        for ticker_ativo, grupo in df_mercado_f.groupby("ticker"):
            grupo_ord = grupo.sort_values("data")
            p_ini = grupo_ord["preco_ajustado"].iloc[0]
            p_fim = grupo_ord["preco_ajustado"].iloc[-1]
            ret_acum = ((p_fim - p_ini) / p_ini) * 100 if p_ini > 0 else 0.0
            vol_med = grupo_ord["volatilidade_21d"].mean()
            vol_fin_tot = grupo_ord["volume_financeiro"].sum()
            setor_ativo = grupo_ord["setor"].iloc[0]

            resumo_ativos.append({
                "ticker": ticker_ativo,
                "setor": setor_ativo,
                "retorno_acumulado": ret_acum,
                "volatilidade_media": vol_med,
                "volume_financeiro_total": vol_fin_tot
            })

        df_resumo_ativos = pd.DataFrame(resumo_ativos)

        # ---------------------------------------------------------------------
        # 2. GRADE OFICIAL DE KPIS ESTRATÉGICOS (LINHA 2)
        # ---------------------------------------------------------------------
        retorno_medio_carteira = df_resumo_ativos["retorno_acumulado"].mean()
        volatilidade_media_carteira = df_resumo_ativos["volatilidade_media"].mean()

        melhor_ativo_row = df_resumo_ativos.loc[df_resumo_ativos["retorno_acumulado"].idxmax()]
        pior_ativo_row = df_resumo_ativos.loc[df_resumo_ativos["retorno_acumulado"].idxmin()]

        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric(
                label="Retorno Médio da Carteira",
                value=f"{retorno_medio_carteira:+.2f}%",
                delta="Rentabilidade Média Ponderada" if len(df_resumo_ativos) > 1 else "Ativo Selecionado",
                help="Média simples da rentabilidade acumulada de todos os ativos sob os filtros ativos."
            )

        with k2:
            st.metric(
                label="Ativo Destaque (Melhor Performance)",
                value=f"{melhor_ativo_row['ticker']}",
                delta=f"{melhor_ativo_row['retorno_acumulado']:+.2f}%",
                help=f"Ativo com maior rentabilidade acumulada no período analisado ({melhor_ativo_row['setor']})."
            )

        with k3:
            st.metric(
                label="Ativo de Menor Performance",
                value=f"{pior_ativo_row['ticker']}",
                delta=f"{pior_ativo_row['retorno_acumulado']:+.2f}%",
                delta_color="inverse" if pior_ativo_row['retorno_acumulado'] < 0 else "normal",
                help=f"Ativo com pior rentabilidade acumulada no período analisado ({pior_ativo_row['setor']})."
            )

        with k4:
            st.metric(
                label="Volatilidade Anualizada Média",
                value=f"{volatilidade_media_carteira:.2f}% a.a.",
                help="Média do desvio-padrão móvel de 21 pregões anualizado (raiz de 252)."
            )

        st.markdown("---")

        # ---------------------------------------------------------------------
        # 3. GRADE OFICIAL DE VISUALIZAÇÕES EM CARDS (LINHA 2)
        # ---------------------------------------------------------------------

        # Card 1: Linha Comparativo Base 100
        with st.container(border=True):
            st.markdown('<div class="card-header-title">1. Performance Normalizada Comparativa (Base 100)</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Séries temporais normalizadas com linha de referência de equilíbrio no nível 100</div>', unsafe_allow_html=True)

            df_base100 = df_mercado_f.copy().sort_values(["ticker", "data"])
            df_base100["base_100_dinamica"] = df_base100.groupby("ticker")["preco_ajustado"].transform(
                lambda x: (x / x.iloc[0]) * 100
            )

            fig_base100 = px.line(
                df_base100,
                x="data",
                y="base_100_dinamica",
                color="ticker",
                labels={"data": "Data do Pregão", "base_100_dinamica": "Índice Base 100", "ticker": "Ativo"}
            )
            fig_base100.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Ponto Neutro (100)")
            fig_base100.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.2))
            
            fig_base100 = formatar_figura_card(fig_base100)
            st.plotly_chart(fig_base100, use_container_width=True)

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            # Card 2: Dispersão Risco vs Retorno
            with st.container(border=True):
                st.markdown('<div class="card-header-title">2. Dispersão Risco × Retorno</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-header-subtitle">Volatilidade Anualizada (% a.a.) no eixo X vs. Retorno Acumulado (%) no eixo Y [Tamanho = Volume]</div>', unsafe_allow_html=True)

                fig_risco_retorno = px.scatter(
                    df_resumo_ativos,
                    x="volatilidade_media",
                    y="retorno_acumulado",
                    color="setor",
                    size="volume_financeiro_total",
                    hover_name="ticker",
                    text="ticker",
                    labels={
                        "volatilidade_media": "Volatilidade Anualizada Móvel (% a.a.)",
                        "retorno_acumulado": "Retorno Acumulado no Período (%)",
                        "volume_financeiro_total": "Volume Financeiro (R$)"
                    }
                )
                fig_risco_retorno.add_hline(y=0, line_dash="solid", line_color="gray")
                fig_risco_retorno.add_vline(x=volatilidade_media_carteira, line_dash="dash", line_color="orange", annotation_text="Vol. Média")
                fig_risco_retorno.update_traces(textposition="top center")
                
                fig_risco_retorno = formatar_figura_card(fig_risco_retorno)
                st.plotly_chart(fig_risco_retorno, use_container_width=True)

        with col_g2:
            # Card 3: Histograma com Boxplot Marginal
            with st.container(border=True):
                st.markdown('<div class="card-header-title">3. Distribuição de Frequência dos Retornos Diários</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-header-subtitle">Distribuição de probabilidade empírica percentual com boxplot marginal para análise de cauda</div>', unsafe_allow_html=True)

                df_ret_hist = df_mercado_f.copy()
                df_ret_hist["retorno_pct"] = df_ret_hist["retorno_diario"] * 100

                fig_hist = px.histogram(
                    df_ret_hist,
                    x="retorno_pct",
                    color="ticker" if st.session_state.filtro_ticker else "setor",
                    marginal="box",
                    nbins=50,
                    labels={"retorno_pct": "Variação Diária (%)"}
                )
                fig_hist.add_vline(x=0, line_dash="dash", line_color="black")
                fig_hist.update_layout(bargap=0.05, legend=dict(orientation="h", y=-0.2))
                
                fig_hist = formatar_figura_card(fig_hist)
                st.plotly_chart(fig_hist, use_container_width=True)

        col_g3, col_g4 = st.columns(2)

        with col_g3:
            # Card 4: Área de Drawdown Histórico
            with st.container(border=True):
                st.markdown('<div class="card-header-title">4. Gráfico de Área de Drawdown Histórico (%)</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-header-subtitle">Queda percentual acumulada a partir do topo histórico (High Watermark) ao longo do tempo</div>', unsafe_allow_html=True)

                fig_drawdown = px.area(
                    df_mercado_f,
                    x="data",
                    y="drawdown",
                    color="ticker",
                    labels={"drawdown": "Drawdown (%)", "data": "Pregão"}
                )
                fig_drawdown.update_layout(legend=dict(orientation="h", y=-0.2))
                
                fig_drawdown = formatar_figura_card(fig_drawdown)
                st.plotly_chart(fig_drawdown, use_container_width=True)

        with col_g4:
            # Card 5: Multilinha de Médias Móveis (SMA 21 e SMA 50)
            with st.container(border=True):
                st.markdown('<div class="card-header-title">5. Médias Móveis de Tendência (SMA 21 e SMA 50)</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-header-subtitle">Preço de Fechamento com sobreposição de médias móveis simples para inspeção técnica</div>', unsafe_allow_html=True)

                if len(st.session_state.filtro_ticker) == 1:
                    ativo_inspecao = st.session_state.filtro_ticker[0]
                else:
                    opcoes_ativos_inspecao = df_resumo_ativos["ticker"].tolist()
                    ativo_inspecao = st.selectbox(
                        "Selecione o ativo para inspeção:",
                        options=opcoes_ativos_inspecao,
                        index=0,
                        key="seletor_ativo_sma"
                    )

                df_sma = df_mercado[df_mercado["ticker"] == ativo_inspecao].copy().sort_values("data")
                df_sma["sma_21"] = df_sma["preco_fechamento"].rolling(window=21).mean()
                df_sma["sma_50"] = df_sma["preco_fechamento"].rolling(window=50).mean()

                if st.session_state.filtro_ano:
                    df_sma = df_sma[df_sma["data"].dt.year.isin(st.session_state.filtro_ano)]

                fig_sma = go.Figure()
                fig_sma.add_trace(go.Scatter(
                    x=df_sma["data"], y=df_sma["preco_fechamento"],
                    name="Preço Fechamento", mode="lines", line=dict(color="#2c3e50", width=1.5)
                ))
                fig_sma.add_trace(go.Scatter(
                    x=df_sma["data"], y=df_sma["sma_21"],
                    name="SMA 21 (Curto Prazo)", mode="lines", line=dict(color="#e67e22", width=2)
                ))
                fig_sma.add_trace(go.Scatter(
                    x=df_sma["data"], y=df_sma["sma_50"],
                    name="SMA 50 (Médio Prazo)", mode="lines", line=dict(color="#2980b9", width=2, dash="dash")
                ))

                fig_sma.update_layout(
                    title=f"Ativo Inspecionado: {ativo_inspecao}",
                    legend=dict(orientation="h", y=-0.2),
                    xaxis_title="Pregão",
                    yaxis_title="Preço Nominal (R$)",
                    hovermode="x unified"
                )
                
                fig_sma = formatar_figura_card(fig_sma)
                st.plotly_chart(fig_sma, use_container_width=True)

        # ---------------------------------------------------------------------
        # 4. STORYTELLING ANALÍTICO
        # ---------------------------------------------------------------------
        st.info(
            f"""
            **Diagnóstico de Risco e Mercado (Linha 2):**
            * **Destaques da Carteira:** A amplitude entre o melhor ativo (**{melhor_ativo_row['ticker']}**, com {melhor_ativo_row['retorno_acumulado']:+.2f}%) e o menor desempenho (**{pior_ativo_row['ticker']}**, com {pior_ativo_row['retorno_acumulado']:+.2f}%) reflete a assimetria setorial perante os ciclos de inflação e commodities.
            * **Risco de Cauda:** O histograma com boxplot marginal evidencia o grau de curtose dos retornos diários, apontando choques intradiários severos em ativos de commodities e varejo.
            * **Sinais de Tendência:** O cruzamento da SMA 21 acima da SMA 50 (Golden Cross) sinaliza momentum positivo de curto prazo, enquanto o afastamento das médias aponta sobrecompra ou sobrevenda técnica.
            """
        )
        
        # =============================================================================
# ABA 3: LINHA 1 - ANÁLISE FUNDAMENTALISTA CORPORATIVA (CVM / DFP)
# =============================================================================
with tab_l1:
    st.subheader("🏢 Linha 1: Análise Fundamentalista Corporativa (CVM / DFP)")
    st.caption("Demonstrações financeiras consolidadas auditadas: rentabilidade, eficiência operacional e solvência.")

    # -------------------------------------------------------------------------
    # 1. CÁLCULO DE KPIS COM DELTA ANUAL DINÂMICO
    # -------------------------------------------------------------------------
    rec_atual_bi = df_balancos_f["receita_liquida"].sum() / 1e9
    lucro_atual_bi = df_balancos_f["lucro_liquido"].sum() / 1e9
    roe_medio_l1 = df_balancos_f["roe"].mean() if not df_balancos_f.empty else 0.0
    
    # Base não financeira para métricas de solvência fabril/comercial
    df_nao_fin_f = df_balancos_f[df_balancos_f["setor"] != "Financeiro"]
    liq_corr_media = df_nao_fin_f["liquidez_corrente"].mean() if not df_nao_fin_f.empty else 0.0

    # Lógica de apuração do Delta Anual (t vs t-1)
    delta_rec_pct = None
    delta_lucro_pct = None
    rotulo_delta = "Consolidado Triênio"

    if len(st.session_state.filtro_ano) == 1:
        ano_selecionado = int(st.session_state.filtro_ano[0])
        if ano_selecionado > 2021:
            ano_anterior = ano_selecionado - 1
            df_comp_ant = df_balancos[df_balancos["ano"] == ano_anterior].copy()

            if st.session_state.filtro_setor:
                df_comp_ant = df_comp_ant[df_comp_ant["setor"].isin(st.session_state.filtro_setor)]
            if st.session_state.filtro_ticker:
                df_comp_ant = df_comp_ant[df_comp_ant["ticker"].isin(st.session_state.filtro_ticker)]

            rec_ant_bi = df_comp_ant["receita_liquida"].sum() / 1e9
            lucro_ant_bi = df_comp_ant["lucro_liquido"].sum() / 1e9

            if rec_ant_bi > 0:
                delta_rec_pct = ((rec_atual_bi - rec_ant_bi) / rec_ant_bi) * 100
            if lucro_ant_bi != 0:
                delta_lucro_pct = ((lucro_atual_bi - lucro_ant_bi) / abs(lucro_ant_bi)) * 100
            
            rotulo_delta = f"vs. {ano_anterior}"
        else:
            rotulo_delta = "Início da Série (2021)"
    elif len(st.session_state.filtro_ano) > 1:
        rotulo_delta = "Consolidado Seleção"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="Receita Líquida Total",
            value=f"R$ {rec_atual_bi:,.1f} Bi",
            delta=f"{delta_rec_pct:+.1f}% {rotulo_delta}" if delta_rec_pct is not None else rotulo_delta,
            help="Soma do faturamento operacional líquido reportado no exercício."
        )

    with c2:
        st.metric(
            label="Lucro Líquido Consolidado",
            value=f"R$ {lucro_atual_bi:,.1f} Bi",
            delta=f"{delta_lucro_pct:+.1f}% {rotulo_delta}" if delta_lucro_pct is not None else rotulo_delta,
            help="Resultado líquido final gerado aos acionistas após impostos e despesas financeiras."
        )

    with c3:
        st.metric(
            label="ROE Médio da Carteira",
            value=f"{roe_medio_l1:.2f}%",
            delta=f"{(roe_medio_l1 - 13.75):+.2f} p.p. vs. Selic Final" if roe_medio_l1 != 0 else None,
            help="Retorno médio sobre o Patrimônio Líquido consolidado das companhias."
        )

    with c4:
        st.metric(
            label="Liquidez Corrente Média",
            value=f"{liq_corr_media:.2f}x",
            help="Capacidade média de pagamento de obrigações de curto prazo (empresas industriais e comerciais)."
        )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 2. GRADE OFICIAL DE VISUALIZAÇÕES EM CARDS (LINHA 1)
    # -------------------------------------------------------------------------

    # Card A: Evolução da Receita Líquida (Largura Total)
    with st.container(border=True):
        st.markdown('<div class="card-header-title">a) Evolução Histórica da Receita Líquida (2021 a 2023)</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-header-subtitle">Faturamento operacional líquido auditado por companhia (R$ Bilhões)</div>', unsafe_allow_html=True)

        df_evol_rec = df_balancos.copy()
        if st.session_state.filtro_setor:
            df_evol_rec = df_evol_rec[df_evol_rec["setor"].isin(st.session_state.filtro_setor)]
        if st.session_state.filtro_ticker:
            df_evol_rec = df_evol_rec[df_evol_rec["ticker"].isin(st.session_state.filtro_ticker)]
        
        df_evol_rec["receita_bi"] = df_evol_rec["receita_liquida"] / 1e9

        fig_barras_rec = px.bar(
            df_evol_rec,
            x="ticker",
            y="receita_bi",
            color="ano",
            barmode="group",
            text_auto=".1f",
            labels={"receita_bi": "Receita Líquida (R$ Bi)", "ticker": "Ativo", "ano": "Exercício Fiscal"},
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_barras_rec.update_layout(xaxis_title="", yaxis_title="Receita Líquida (R$ Bi)")
        
        fig_barras_rec = formatar_figura_card(fig_barras_rec)
        st.plotly_chart(fig_barras_rec, use_container_width=True)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        # Card B: Treemap Setorial da Receita
        with st.container(border=True):
            st.markdown('<div class="card-header-title">b) Distribuição Setorial da Receita Líquida</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Representatividade econômica relativa dos setores na carteira (R$ Bi)</div>', unsafe_allow_html=True)

            df_setor_comp = df_balancos_f.groupby("setor")["receita_liquida"].sum().reset_index()
            df_setor_comp["receita_bi"] = df_setor_comp["receita_liquida"] / 1e9

            fig_tree = px.treemap(
                df_setor_comp,
                path=["setor"],
                values="receita_bi",
                color="receita_bi",
                color_continuous_scale="Teal"
            )
            fig_tree.update_traces(textinfo="label+value+percent root")
            
            fig_tree = formatar_figura_card(fig_tree)
            st.plotly_chart(fig_tree, use_container_width=True)

    with col_g2:
        # Card C: Quadrante Margem Líquida vs. ROE
        with st.container(border=True):
            st.markdown('<div class="card-header-title">c) Quadrante Estratégico: Margem Líquida vs. ROE</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Rentabilidade líquida das vendas (%) vs. Retorno sobre o PL acionário (%)</div>', unsafe_allow_html=True)

            fig_quad = px.scatter(
                df_balancos_f,
                x="margem_liquida",
                y="roe",
                color="setor",
                size="receita_liquida",
                hover_name="ticker",
                hover_data=["empresa", "ano", "lucro_liquido"],
                labels={"margem_liquida": "Margem Líquida (%)", "roe": "ROE (%)"}
            )
            fig_quad.add_hline(y=13.75, line_dash="dash", line_color="red", annotation_text="Custo Selic (13.75%)")
            fig_quad.add_vline(x=0, line_dash="dash", line_color="gray")
            fig_quad.add_hline(y=0, line_dash="solid", line_color="gray")
            
            fig_quad = formatar_figura_card(fig_quad)
            st.plotly_chart(fig_quad, use_container_width=True)

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        # Card D: Boxplot da Margem EBIT por Setor
        with st.container(border=True):
            st.markdown('<div class="card-header-title">d) Dispersão da Margem EBIT por Setor (Boxplot)</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Variabilidade e assimetria do retorno operacional livre de encargos financeiros</div>', unsafe_allow_html=True)

            fig_box = px.box(
                df_balancos_f[df_balancos_f["setor"] != "Financeiro"],
                x="setor",
                y="margem_ebit",
                color="setor",
                points="all",
                labels={"margem_ebit": "Margem EBIT (%)", "setor": "Segmento"}
            )
            fig_box.update_layout(showlegend=False, xaxis_title="", yaxis_title="Margem EBIT (%)")
            
            fig_box = formatar_figura_card(fig_box)
            st.plotly_chart(fig_box, use_container_width=True)

    with col_g4:
        # Card E: Matriz de Solvência e Risco Corporativo com Quadrantes Sombreados
        with st.container(border=True):
            st.markdown('<div class="card-header-title">e) Matriz de Solvência e Risco Corporativo</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Liquidez Corrente (x) vs. Dívida Líquida (R$ Bi) com delimitação de risco</div>', unsafe_allow_html=True)

            df_solv = df_nao_fin_f.copy()

            if df_solv.empty:
                st.info("Nenhuma companhia não-financeira selecionada para avaliação de solvência.")
            else:
                df_solv["divida_liquida_bi"] = (df_solv["divida_liquida"] / 1e9).round(2)
                df_solv["liquidez_corrente"] = df_solv["liquidez_corrente"].round(2)

                x_min = max(0.0, df_solv["liquidez_corrente"].min() - 0.2)
                x_max = max(3.0, df_solv["liquidez_corrente"].max() + 0.3)
                y_min = df_solv["divida_liquida_bi"].min() - 2.0
                y_max = df_solv["divida_liquida_bi"].max() + 5.0

                fig_matriz_solv = go.Figure()

                # Quadrante 1: Alerta de Insolvência (Liquidez < 1.0 e Dívida > 0)
                fig_matriz_solv.add_shape(
                    type="rect",
                    x0=0, x1=1.0,
                    y0=0, y1=y_max,
                    fillcolor="#e74c3c",
                    opacity=0.20,
                    layer="below",
                    line_width=0
                )

                # Quadrante 2: Fortaleza Financeira (Liquidez > 1.0 e Dívida < 0)
                fig_matriz_solv.add_shape(
                    type="rect",
                    x0=1.0, x1=x_max,
                    y0=y_min, y1=0,
                    fillcolor="#27ae60",
                    opacity=0.20,
                    layer="below",
                    line_width=0
                )

                fig_matriz_solv.add_vline(x=1.0, line_dash="dash", line_color="#bdc3c7", line_width=1.5)
                fig_matriz_solv.add_hline(y=0.0, line_dash="solid", line_color="#7f8c8d", line_width=1.5)

                fig_matriz_solv.add_trace(go.Scatter(
                    x=df_solv["liquidez_corrente"],
                    y=df_solv["divida_liquida_bi"],
                    mode="markers+text",
                    text=df_solv["ticker"],
                    textposition="top right",
                    textfont=dict(size=11, color="#1e293b"),
                    marker=dict(
                        size=12,
                        color="#3498db",
                        line=dict(width=1.5, color="#ffffff")
                    ),
                    name="Companhias",
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "Liquidez Corrente: %{x:.2f}x<br>"
                        "Dívida Líquida: R$ %{y:.2f} Bi<extra></extra>"
                    )
                ))

                fig_matriz_solv.add_annotation(
                    x=0.5, y=y_max * 0.92,
                    text="<i>Alerta de Insolvência</i>",
                    showarrow=False,
                    font=dict(color="#c0392b", size=12, family="Segoe UI")
                )
                fig_matriz_solv.add_annotation(
                    x=(x_max + 1.0) / 2, y=y_min * 0.75,
                    text="<i>Fortaleza Financeira</i>",
                    showarrow=False,
                    font=dict(color="#27ae60", size=12, family="Segoe UI")
                )

                fig_matriz_solv.update_layout(
                    xaxis=dict(title="Liquidez Corrente (x)", range=[0, x_max], showgrid=True, gridcolor="#f1f5f9"),
                    yaxis=dict(title="Dívida Líquida (R$ Bi)", range=[y_min, y_max], showgrid=True, gridcolor="#f1f5f9"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
                )

                fig_matriz_solv = formatar_figura_card(fig_matriz_solv)
                st.plotly_chart(fig_matriz_solv, use_container_width=True)

    # -------------------------------------------------------------------------
    # 3. STORYTELLING ANALÍTICO E LIMITAÇÕES DA METODOLOGIA
    # -------------------------------------------------------------------------
    st.info(
        """
        **Interpretação e Rastreabilidade Fundamentalista:**
        * **Eficiência de Capital:** O quadrante superior direito (Margem Líquida alta e ROE > 13,75%) concentra companhias com vantagens competitivas sustentáveis perante a taxa básica de juros.
        * **Resiliência de Solvência:** Índices de Liquidez Corrente superiores a 1,0x indicam cobertura folgada de passivos circulantes pelo ativo realizável de curto prazo.
        * **Nota Técnica Metodológica:** Instituições financeiras (`ITUB4` e `BBDC4`) são automaticamente excluídas dos gráficos de Margem EBIT e Dívida Líquida/Liquidez Corrente por adotarem o plano contábil COSIF/BACEN, no qual a intermediação financeira compõe a atividade operacional direta.
        """
    )
    
    # =============================================================================
# ABA 4: LINHA 3 - INTELIGÊNCIA MACROECONÔMICA (BACEN / SGS)
# =============================================================================
with tab_l3:
    st.subheader("🏦 Linha 3: Inteligência Macroeconômica e Indicadores Financeiros (BACEN / SGS)")
    st.caption("Acompanhamento das metas de política monetária, ancoragem inflacionária, câmbio e atividade econômica.")

    # -------------------------------------------------------------------------
    # 1. PROCESSAMENTO DE KPIS MACRO COM DELTAS DINÂMICOS
    # -------------------------------------------------------------------------
    if len(st.session_state.filtro_ano) == 1:
        ano_macro_sel = int(st.session_state.filtro_ano[0])
    else:
        ano_macro_sel = 2023
    
    df_macro_ano_atual = df_macro[df_macro["referencia_mensal"].dt.year == ano_macro_sel].sort_values("referencia_mensal")
    df_macro_ano_ant = df_macro[df_macro["referencia_mensal"].dt.year == (ano_macro_sel - 1)].sort_values("referencia_mensal")

    selic_val = df_macro_ano_atual["selic_meta"].iloc[-1] if not df_macro_ano_atual.empty else 11.75
    ipca_val = df_macro_ano_atual["ipca_12m"].iloc[-1] if not df_macro_ano_atual.empty else 4.62
    juro_real_val = df_macro_ano_atual["juro_real_ex_post"].iloc[-1] if not df_macro_ano_atual.empty else 6.81
    ptax_val = df_macro_ano_atual["dolar_ptax"].iloc[-1] if not df_macro_ano_atual.empty else 4.84

    if not df_macro_ano_ant.empty:
        delta_selic_val = selic_val - df_macro_ano_ant["selic_meta"].iloc[-1]
        delta_ipca_val = ipca_val - df_macro_ano_ant["ipca_12m"].iloc[-1]
        delta_juro_val = juro_real_val - df_macro_ano_ant["juro_real_ex_post"].iloc[-1]
        delta_ptax_val = ((ptax_val - df_macro_ano_ant["dolar_ptax"].iloc[-1]) / df_macro_ano_ant["dolar_ptax"].iloc[-1]) * 100
        rotulo_macro_delta = f"vs. {ano_macro_sel - 1}"
    else:
        delta_selic_val = delta_ipca_val = delta_juro_val = delta_ptax_val = None
        rotulo_macro_delta = "Marco Base (2019)"

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            label="Taxa Selic Meta Vigente",
            value=f"{selic_val:.2f}% a.a.",
            delta=f"{delta_selic_val:+.2f} p.p. {rotulo_macro_delta}" if delta_selic_val is not None else rotulo_macro_delta,
            help="Taxa básica de juros fixada pelo COPOM ao término do período."
        )

    with m2:
        st.metric(
            label="IPCA Acumulado 12 Meses",
            value=f"{ipca_val:.2f}% a.a.",
            delta=f"{delta_ipca_val:+.2f} p.p. {rotulo_macro_delta}" if delta_ipca_val is not None else rotulo_macro_delta,
            delta_color="inverse",
            help="Inflação oficial acumulada em 12 meses (SGS 13522)."
        )

    with m3:
        st.metric(
            label="Juro Real Ex-Post de Fisher",
            value=f"{juro_real_val:.2f}% a.a.",
            delta=f"{delta_juro_val:+.2f} p.p. {rotulo_macro_delta}" if delta_juro_val is not None else rotulo_macro_delta,
            help="Taxa real de juros calculada pela Equação de Fisher: [(1 + Selic)/(1 + IPCA 12M) - 1] * 100."
        )

    with m4:
        st.metric(
            label="Taxa de Câmbio Dólar PTAX",
            value=f"R$ {ptax_val:.2f}",
            delta=f"{delta_ptax_val:+.2f}% {rotulo_macro_delta}" if delta_ptax_val is not None else rotulo_macro_delta,
            delta_color="inverse",
            help="Cotação comercial de fechamento do Dólar americano calculada pelo BACEN (SGS 1)."
        )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 2. GRADE OFICIAL DE VISUALIZAÇÕES EM CARDS (LINHA 3)
    # -------------------------------------------------------------------------
    df_plot_macro = df_macro.copy() if not st.session_state.filtro_ano else df_macro_f.copy()

    # Card 1: Gráfico Combinado de Política Monetária (Largura Total)
    with st.container(border=True):
        st.markdown('<div class="card-header-title">1. Gráfico Combinado de Política Monetária</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-header-subtitle">Selic Meta (% a.a.), IPCA 12M (% a.a.) e Juro Real Ex-Post em barras no mesmo plano</div>', unsafe_allow_html=True)

        fig_pol_monetaria = go.Figure()
        fig_pol_monetaria.add_trace(go.Bar(
            x=df_plot_macro["referencia_mensal"],
            y=df_plot_macro["juro_real_ex_post"],
            name="Juro Real Ex-Post (% a.a.)",
            marker_color="rgba(46, 204, 113, 0.45)",
            marker_line_color="rgb(39, 174, 96)",
            marker_line_width=1
        ))
        fig_pol_monetaria.add_trace(go.Scatter(
            x=df_plot_macro["referencia_mensal"],
            y=df_plot_macro["selic_meta"],
            name="Selic Meta (% a.a.)",
            mode="lines+markers",
            line=dict(color="#2980b9", width=3)
        ))
        fig_pol_monetaria.add_trace(go.Scatter(
            x=df_plot_macro["referencia_mensal"],
            y=df_plot_macro["ipca_12m"],
            name="IPCA 12M (% a.a.)",
            mode="lines",
            line=dict(color="#e74c3c", width=2, dash="dot")
        ))

        fig_pol_monetaria.add_hline(y=0, line_dash="solid", line_color="gray")
        fig_pol_monetaria.update_layout(
            legend=dict(orientation="h", y=-0.2),
            xaxis_title="Competência Mensal",
            yaxis_title="Taxa (% a.a.)",
            hovermode="x unified"
        )
        
        fig_pol_monetaria = formatar_figura_card(fig_pol_monetaria)
        st.plotly_chart(fig_pol_monetaria, use_container_width=True)

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        # Card 2: Linha Cambial com Média Histórica
        with st.container(border=True):
            st.markdown('<div class="card-header-title">2. Dinâmica do Dólar PTAX com Média Histórica</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Evolução do câmbio comercial (R$) com patamar médio horizontal do período</div>', unsafe_allow_html=True)

            media_ptax = df_plot_macro["dolar_ptax"].mean()

            fig_ptax = px.line(
                df_plot_macro,
                x="referencia_mensal",
                y="dolar_ptax",
                labels={"referencia_mensal": "Data", "dolar_ptax": "Dólar PTAX (R$)"}
            )
            fig_ptax.update_traces(line_color="#e67e22", line_width=2.5)
            fig_ptax.add_hline(
                y=media_ptax,
                line_dash="dash",
                line_color="#2c3e50",
                annotation_text=f"Média: R$ {media_ptax:.2f}"
            )
            fig_ptax.update_layout(xaxis_title="", yaxis_title="Câmbio Comercial (R$)")
            
            fig_ptax = formatar_figura_card(fig_ptax)
            st.plotly_chart(fig_ptax, use_container_width=True)

    with col_m2:
        # Card 3: Dispersão Macroeconômica Dólar vs. IPCA
        with st.container(border=True):
            st.markdown('<div class="card-header-title">3. Dispersão: Dólar PTAX vs. IPCA 12M</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Confronto de pass-through cambial e inflação [Tamanho = Taxa Selic]</div>', unsafe_allow_html=True)

            df_disp_macro = df_plot_macro.copy()
            df_disp_macro["ano_str"] = df_disp_macro["referencia_mensal"].dt.year.astype(str)

            fig_disp_macro = px.scatter(
                df_disp_macro,
                x="dolar_ptax",
                y="ipca_12m",
                color="ano_str",
                size="selic_meta",
                hover_data=["referencia_mensal", "selic_meta", "juro_real_ex_post"],
                labels={
                    "dolar_ptax": "Câmbio PTAX (R$)",
                    "ipca_12m": "Inflação IPCA 12M (%)",
                    "ano_str": "Exercício"
                },
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            
            fig_disp_macro = formatar_figura_card(fig_disp_macro)
            st.plotly_chart(fig_disp_macro, use_container_width=True)

    col_m3, col_m4 = st.columns(2)

    with col_m3:
        # Card 4: IBC-Br Dessazonalizado
        with st.container(border=True):
            st.markdown('<div class="card-header-title">4. Atividade Econômica Real: IBC-Br Dessazonalizado</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Evolução do índice proxy mensal do PIB calculado pelo Banco Central</div>', unsafe_allow_html=True)

            fig_ibc = px.line(
                df_plot_macro,
                x="referencia_mensal",
                y="ibc_br",
                labels={"referencia_mensal": "Data", "ibc_br": "Índice (Número-Índice)"}
            )
            fig_ibc.update_traces(line_color="#8e44ad", line_width=2.5)
            fig_ibc.update_layout(xaxis_title="", yaxis_title="IBC-Br Dessazonalizado")
            
            fig_ibc = formatar_figura_card(fig_ibc)
            st.plotly_chart(fig_ibc, use_container_width=True)

    with col_m4:
        # Card 5: Heatmap de Pearson
        with st.container(border=True):
            st.markdown('<div class="card-header-title">5. Matriz de Correlação Linear de Pearson</div>', unsafe_allow_html=True)
            st.markdown('<div class="card-header-subtitle">Associação estatística linear com anotações automáticas entre variáveis</div>', unsafe_allow_html=True)

            cols_macro = ["selic_meta", "ipca_12m", "juro_real_ex_post", "dolar_ptax", "ibc_br"]
            df_corr = df_plot_macro[cols_macro].rename(columns={
                "selic_meta": "Selic",
                "ipca_12m": "IPCA 12M",
                "juro_real_ex_post": "Juro Real",
                "dolar_ptax": "PTAX",
                "ibc_br": "IBC-Br"
            }).corr().round(2)

            fig_corr = px.imshow(
                df_corr,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1
            )
            fig_corr.update_layout(coloraxis_colorbar=dict(title="Pearson (r)"))
            
            fig_corr = formatar_figura_card(fig_corr)
            st.plotly_chart(fig_corr, use_container_width=True)

    # -------------------------------------------------------------------------
    # 3. STORYTELLING ANALÍTICO E LIMITAÇÕES
    # -------------------------------------------------------------------------
    st.info(
        """
        **Diagnóstico Macroeconômico e Considerações Metodológicas (Linha 3):**
        * **Choque de Juros e Defasagem Temporal:** A escalada da Selic de 2,00% (2020/2021) para 13,75% (2022/2023) gerou um expressivo aumento do Juro Real Ex-Post, superando 6,5% a.a. no final do ciclo e ancorando as expectativas inflacionárias (IPCA desacelerando de >10% para ~4,6%).
        * **Câmbio e Atividade:** O Dólar PTAX oscilou em torno da média de R\$ 5,10 a R\$ 5,20 no quinquênio, refletindo choques fiscais domésticos e aversão ao risco global. O IBC-Br demonstrou recuperação pós-2020 com posterior desaceleração decorrente do encarecimento do crédito.
        * **Ressalva Estatística:** A correlação de Pearson afere estritamente a associação linear entre séries históricas concomitantes; não implica causalidade unilateral e deve ser interpretada considerando a defasagem temporal da transmissão da política monetária (de 6 a 18 meses).
        """
    )

# =============================================================================
# ABA 5: BASE DE DADOS & EXPORTAÇÃO
# =============================================================================
with tab_exp:
    st.subheader("💾 Base de Dados Consolidada da Tríade")
    st.caption("Visão tabular integrada para auditoria e validação de consistência.")

    with st.container(border=True):
        st.markdown('<div class="card-header-title">Tabela Cadastral e Financeira Integrada (Tríade)</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card-header-subtitle">Registros ativos após os filtros aplicados: <b>{len(df_triade_f)} observações</b> | Variáveis: <b>{len(df_triade_f.columns)} colunas</b>.</div>',
            unsafe_allow_html=True
        )

        st.dataframe(df_triade_f, use_container_width=True)

        csv_bytes = df_triade_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar Base Filtrada (CSV)",
            data=csv_bytes,
            file_name="triade_financeira_filtrada.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        

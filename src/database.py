"""
Módulo de Conexão Resiliente e Fallback em CSV
Projeto: Plataforma Financeira Integrada (Tríade)
Aluno: Orlando Vieira de Castro Junior
"""

from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"


@st.cache_data(ttl=3600, show_spinner=False)
def carregar_tabela_resiliente(nome_tabela: str) -> tuple[pd.DataFrame, str]:
    """
    Tenta carregar os dados via PostgreSQL (Supabase).
    Caso ocorra falha de rede ou falta de credenciais, aciona contingência local lendo o CSV.
    """
    # 1. Tentativa Primária: Supabase (PostgreSQL)
    try:
        conn = st.connection("postgresql", type="sql")
        query = f"SELECT * FROM {nome_tabela};"
        df = conn.query(query, ttl=3600)
        if df is not None and not df.empty:
            return df, "Supabase (PostgreSQL)"
    except Exception as erro:
        # Registra no log sem interromper a execução do Data App
        print(f"[AVISO CONTINGÊNCIA] Falha ao consultar '{nome_tabela}' no Supabase: {erro}")

    # 2. Tentativa Secundária: Contingência Local (CSV)
    caminho_csv = PROCESSED_DATA_DIR / f"{nome_tabela}.csv"
    if caminho_csv.exists():
        df_csv = pd.read_csv(caminho_csv)
        return df_csv, "Contingência Local (CSV)"

    raise FileNotFoundError(
        f"Erro Crítico: Não foi possível carregar a tabela '{nome_tabela}' nem via Supabase nem via CSV."
    )


def carregar_dados_completos() -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """Carrega o ecossistema completo de dados da plataforma."""
    tabelas = ["macro_bacen", "mercado_b3", "balancos_cvm", "triade_consolidada"]
    dfs = {}
    fontes = {}

    for tabela in tabelas:
        df, fonte = carregar_tabela_resiliente(tabela)
        dfs[tabela] = df
        fontes[tabela] = fonte

    return dfs, fontes
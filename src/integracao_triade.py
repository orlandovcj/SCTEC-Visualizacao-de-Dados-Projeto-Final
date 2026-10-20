"""
Módulo de Integração Analítica e Modelagem Dimensional (Tríade: Macro + Mercado + Balanços)
Projeto: Plataforma Financeira Integrada (Tríade)
Aluno: Orlando Vieira de Castro Junior
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Caminhos relativos ao diretório raiz
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"


def carregar_bases_processadas() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega as bases individuais geradas nas etapas anteriores do pipeline."""
    caminho_macro = PROCESSED_DATA_DIR / "macro_bacen.csv"
    caminho_mercado = PROCESSED_DATA_DIR / "mercado_b3.csv"
    caminho_balancos = PROCESSED_DATA_DIR / "balancos_cvm.csv"

    for caminho in [caminho_macro, caminho_mercado, caminho_balancos]:
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não localizado em data/processed: {caminho.name}")

    df_macro = pd.read_csv(caminho_macro)
    df_mercado = pd.read_csv(caminho_mercado)
    df_balancos = pd.read_csv(caminho_balancos)

    return df_macro, df_mercado, df_balancos


def agregar_macro_anual(df_macro: pd.DataFrame) -> pd.DataFrame:
    """Consolida as séries do BACEN em médias e acumulados anuais."""
    df = df_macro.copy()
    df["ano"] = pd.to_datetime(df["referencia_mensal"]).dt.year

    # Filtrar anos de foco da Tríade (2019 a 2023)
    df_triade = df[df["ano"].isin([2019, 2020, 2021, 2022, 2023])].copy()

    macro_anual = df_triade.groupby("ano").agg(
        selic_media_ano=("selic_meta", "mean"),
        selic_fim_ano=("selic_meta", "last"),
        ipca_acum_ano=("ipca_12m", "last"),
        juro_real_fim_ano=("juro_real_ex_post", "last"),
        dolar_medio_ano=("dolar_ptax", "mean"),
        dolar_fim_ano=("dolar_ptax", "last"),
        ibc_br_medio=("ibc_br", "mean")
    ).reset_index()

    return macro_anual.round(2)


def agregar_mercado_anual(df_mercado: pd.DataFrame) -> pd.DataFrame:
    """Calcula o retorno acumulado anual e volatilidade média de cada ação na B3."""
    df = df_mercado.copy()
    df["data"] = pd.to_datetime(df["data"])
    df["ano"] = df["data"].dt.year
    df.sort_values(by=["ticker", "data"], inplace=True)

    registros = []
    for (ticker, ano), grupo in df.groupby(["ticker", "ano"]):
        if grupo.empty:
            continue

        preco_inicial = grupo["preco_ajustado"].iloc[0]
        preco_final = grupo["preco_ajustado"].iloc[-1]
        retorno_ano = ((preco_final - preco_inicial) / preco_inicial) * 100
        volatilidade_media = grupo["volatilidade_21d"].mean()
        drawdown_pior = grupo["drawdown"].min()
        volume_total = grupo["volume_financeiro"].sum()

        registros.append({
            "ticker": ticker,
            "ano": ano,
            "preco_fechamento_ano": round(preco_final, 2),
            "retorno_anual_b3": round(retorno_ano, 2),
            "volatilidade_media_ano": round(volatilidade_media, 2),
            "drawdown_maximo_ano": round(drawdown_pior, 2),
            "volume_anual_negociado": volume_total
        })

    return pd.DataFrame(registros)


def gerar_base_triade():
    """Realiza o cruzamento relacional das três dimensões."""
    print("Iniciando integração da Tríade Financeira...")
    df_macro, df_mercado, df_balancos = carregar_bases_processadas()

    df_macro_anual = agregar_macro_anual(df_macro)
    df_mercado_anual = agregar_mercado_anual(df_mercado)

    # 1. Cruzar Balanços CVM com Performance de Mercado B3 por Ticker e Ano
    df_integrado = pd.merge(
        df_balancos,
        df_mercado_anual,
        on=["ticker", "ano"],
        how="inner"
    )

    # 2. Cruzar com Indicadores Macroeconômicos BACEN por Ano
    df_triade = pd.merge(
        df_integrado,
        df_macro_anual,
        on="ano",
        how="inner"
    )

    # Exportação tratada com caminho relativo
    caminho_saida = PROCESSED_DATA_DIR / "triade_consolidada.csv"
    df_triade.to_csv(caminho_saida, index=False)

    print(f"Base consolidada da Tríade gerada com sucesso!")
    print(f"Total de registros: {len(df_triade)} linhas e {len(df_triade.columns)} colunas.")
    print(f"Arquivo salvo em: {caminho_saida}")
    return df_triade


if __name__ == "__main__":
    gerar_base_triade()
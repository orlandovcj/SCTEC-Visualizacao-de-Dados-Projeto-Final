"""
Módulo de Extração, Transformação e Carga (ETL) - Indicadores Macroeconômicos SGS/BACEN
Projeto: Plataforma Financeira Integrada (Tríade)
Aluno: Orlando Vieira de Castro Junior
"""

from pathlib import Path
import requests
import pandas as pd
import numpy as np

# Configuração de caminhos relativos ao diretório raiz do repositório
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# Dicionário de séries oficiais do BACEN conforme requisitos
SERIES_BACEN = {
    "selic_meta": 432,       # Taxa Selic anualizada (% a.a.)
    "ipca_mensal": 433,      # IPCA variação mensal (%)
    "ipca_12m": 13522,       # IPCA acumulado 12 meses (%)
    "dolar_ptax": 1,         # Dólar Comercial Venda (R$)
    "ibc_br": 24364          # Índice de Atividade Económica Dessazonalizado
}

DATA_INICIAL = "01/01/2019"
DATA_FINAL = "31/12/2023"


def extrair_serie_sgs(codigo_serie: int, data_inicial: str, data_final: str) -> pd.DataFrame:
    """Extrai uma série temporal específica da API pública do SGS/BACEN."""
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados"
        f"?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        resposta = requests.get(url, headers=headers, timeout=30)
        resposta.raise_for_status()
        dados = resposta.json()
        df = pd.DataFrame(dados)
        return df
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Falha ao consultar série {codigo_serie} no SGS/BACEN: {e}")


def executar_pipeline_macro() -> pd.DataFrame:
    """Executa a extração, tratamento, harmonização mensal e cálculo de métricas derivadas."""
    print("Iniciando extração de séries temporais do BACEN...")
    dfs = {}

    for nome, codigo in SERIES_BACEN.items():
        print(f"Extraindo série {nome} (Código: {codigo})...")
        df_serie = extrair_serie_sgs(codigo, DATA_INICIAL, DATA_FINAL)
        
        # Conversão de tipos e validação
        df_serie["data"] = pd.to_datetime(df_serie["data"], format="%d/%m/%Y")
        df_serie["valor"] = pd.to_numeric(df_serie["valor"], errors="coerce")
        
        # Guardar cópia em cache local bruto
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        df_serie.to_csv(RAW_DATA_DIR / f"bacen_{nome}_bruto.csv", index=False)
        
        dfs[nome] = df_serie

    # Harmonização temporal por frequência mensal (último valor observado no mês)
    print("Harmonizando séries temporais para granularidade mensal...")
    
    # Criar grelha temporal mensal (último dia do mês)
    datas_mensais = pd.date_range(start="2019-01-01", end="2023-12-31", freq="ME")
    df_consolidado = pd.DataFrame({"referencia_mensal": datas_mensais})
    df_consolidado["ano_mes"] = df_consolidado["referencia_mensal"].dt.to_period("M")

    for nome, df_origem in dfs.items():
        df_temp = df_origem.dropna(subset=["valor"]).copy()
        df_temp["ano_mes"] = df_temp["data"].dt.to_period("M")
        
        # Obter o último valor disponível em cada competência mensal
        df_mensal = df_temp.sort_values("data").groupby("ano_mes")["valor"].last().reset_index()
        df_mensal.rename(columns={"valor": nome}, inplace=True)
        
        df_consolidado = pd.merge(df_consolidado, df_mensal, on="ano_mes", how="left")

    # Tratamento de valores ausentes por propagação temporal controlada
    df_consolidado.ffill(inplace=True)
    df_consolidado.bfill(inplace=True)

    # Cálculo da métrica financeira: Juro Real Ex-Post (% a.a.) via Equação de Fisher
    df_consolidado["juro_real_ex_post"] = (
        ((1 + (df_consolidado["selic_meta"] / 100)) / (1 + (df_consolidado["ipca_12m"] / 100))) - 1
    ) * 100
    df_consolidado["juro_real_ex_post"] = df_consolidado["juro_real_ex_post"].round(2)

    # Seleção de campos e formatação final
    df_final = df_consolidado[[
        "referencia_mensal",
        "selic_meta",
        "ipca_mensal",
        "ipca_12m",
        "juro_real_ex_post",
        "dolar_ptax",
        "ibc_br"
    ]].copy()

    # Exportação tratada com caminho relativo
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    caminho_saida = PROCESSED_DATA_DIR / "macro_bacen.csv"
    df_final.to_csv(caminho_saida, index=False)
    
    print(f"Pipeline concluído com sucesso. Arquivo gravado em: {caminho_saida}")
    return df_final


if __name__ == "__main__":
    executar_pipeline_macro()
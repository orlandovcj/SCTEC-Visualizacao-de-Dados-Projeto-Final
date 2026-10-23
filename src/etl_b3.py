"""
Módulo de Extração, Transformação e Carga (ETL) - Mercado de Ações (B3 / yfinance)
Projeto: Plataforma Financeira Integrada (Tríade)
Aluno: Orlando Vieira de Castro Junior
"""

from pathlib import Path
import time
import pandas as pd
import numpy as np
import yfinance as yf
import requests

# Configuração de caminhos relativos ao diretório raiz do repositório
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# Dicionário de ativos com setores correspondentes
ATIVOS_B3 = {
    "WEGE3.SA": {"ticker": "WEGE3", "setor": "Bens Industriais"},
    "EMBJ3.SA": {"ticker": "EMBJ3", "setor": "Bens Industriais"},  # Histórico EMBR3
    "VALE3.SA": {"ticker": "VALE3", "setor": "Materiais Básicos"},
    "GGBR4.SA": {"ticker": "GGBR4", "setor": "Materiais Básicos"},
    "KLBN11.SA": {"ticker": "KLBN11", "setor": "Materiais Básicos"},
    "SUZB3.SA": {"ticker": "SUZB3", "setor": "Materiais Básicos"},
    "PETR4.SA": {"ticker": "PETR4", "setor": "Petróleo e Gás"},
    "PRIO3.SA": {"ticker": "PRIO3", "setor": "Petróleo e Gás"},
    "EGIE3.SA": {"ticker": "EGIE3", "setor": "Energia Elétrica"},
    "ITUB4.SA": {"ticker": "ITUB4", "setor": "Financeiro"},
    "BBDC4.SA": {"ticker": "BBDC4", "setor": "Financeiro"},
    "ABEV3.SA": {"ticker": "ABEV3", "setor": "Consumo Não Cíclico"},
    "JBSS32.SA": {"ticker": "JBSS32", "setor": "Consumo Não Cíclico"}, # Em junho de 2025 JBSS3 foi deslistada, eJBSS32 virou a ação principal.
    "RENT3.SA": {"ticker": "RENT3", "setor": "Consumo Cíclico"},
    "LREN3.SA": {"ticker": "LREN3", "setor": "Consumo Cíclico"}
}

DATA_INICIAL = "2019-01-01"
DATA_FINAL = "2023-12-31"


def obter_sessao_http() -> requests.Session:
    """Cria uma sessão HTTP estruturada para contornar bloqueios do Yahoo Finance."""
    sessao = requests.Session()
    sessao.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    return sessao


def extrair_ativo_com_retry(ticker_sa: str, inicio: str, fim: str, max_tentativas: int = 3) -> pd.DataFrame:
    """Extrai as cotações diárias completas (OHLCV) de um único ativo com retries."""
    sessao = obter_sessao_http()
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            ativo = yf.Ticker(ticker_sa, session=sessao)
            df = ativo.history(start=inicio, end=fim, auto_adjust=False)
            
            if not df.empty and "Open" in df.columns:
                return df
            
            # Tentativa alternativa com download direto
            df = yf.download(
                tickers=ticker_sa,
                start=inicio,
                end=fim,
                auto_adjust=False,
                progress=False,
                session=sessao
            )
            if not df.empty and "Open" in df.columns:
                return df
                
        except Exception as e:
            print(f"Tentativa {tentativa}/{max_tentativas} falhou para {ticker_sa}: {e}")
            time.sleep(1.5)
            
    return pd.DataFrame()


def calcular_indicadores_ativo(df_ativo: pd.DataFrame, ticker: str, setor: str) -> pd.DataFrame:
    """Calcula métricas padronizadas e preserva variáveis OHLCV obrigatórias."""
    df = df_ativo.copy()
    
    # Tratamento caso venha MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.reset_index(inplace=True)
    
    col_data = "Date" if "Date" in df.columns else "data"
    df.dropna(subset=["Adj Close", "Close", "Open", "High", "Low"], inplace=True)
    df.sort_values(by=col_data, inplace=True)
    
    if df.empty:
        return pd.DataFrame()

    # Variáveis Padronizadas Obrigatórias pelo Edital (Item 4.1.1-B)
    df["data"] = pd.to_datetime(df[col_data]).dt.date
    df["ticker"] = ticker
    df["setor"] = setor
    df["abertura"] = df["Open"].round(2)
    df["maxima"] = df["High"].round(2)
    df["minima"] = df["Low"].round(2)
    df["preco_fechamento"] = df["Close"].round(2)
    df["preco_ajustado"] = df["Adj Close"].round(4)
    df["volume_financeiro"] = df["Volume"].astype(float)

    # 1. Retorno Diário Simples
    df["retorno_diario"] = df["preco_ajustado"].pct_change()

    # 2. Base 100 (Normalização temporal)
    preco_base = df["preco_ajustado"].iloc[0]
    df["base_100"] = ((df["preco_ajustado"] / preco_base) * 100).round(2)

    # 3. Drawdown Histórico
    pico = df["preco_ajustado"].cummax()
    df["drawdown"] = (((df["preco_ajustado"] - pico) / pico) * 100).round(2)

    # 4. Volatilidade Móvel Anualizada (21 pregões úteis)
    df["volatilidade_21d"] = (
        df["retorno_diario"].rolling(window=21).std() * np.sqrt(252) * 100
    ).round(2)

    colunas_finais = [
        "data", "ticker", "setor", 
        "abertura", "maxima", "minima", "preco_fechamento", "preco_ajustado",
        "volume_financeiro", "retorno_diario", "base_100", "drawdown", "volatilidade_21d"
    ]
    return df[colunas_finais]


def executar_pipeline_b3():
    """Executa a coleta e cálculo das variáveis OHLCV e métricas de mercado."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    registros_processados = []
    print(f"Iniciando coleta com inclusão de OHLCV para {len(ATIVOS_B3)} ativos...")

    for ticker_sa, info in ATIVOS_B3.items():
        ticker_puro = info["ticker"]
        setor = info["setor"]
        print(f"Extraindo dados de {ticker_puro} ({ticker_sa})...")

        df_bruto = extrair_ativo_com_retry(ticker_sa, DATA_INICIAL, DATA_FINAL)
        
        if df_bruto.empty:
            print(f"ALERTA: Falha na extração de {ticker_sa}.")
            continue

        # Processamento com campos OHLCV
        df_tratado = calcular_indicadores_ativo(df_bruto, ticker_puro, setor)
        if not df_tratado.empty:
            registros_processados.append(df_tratado)

        time.sleep(0.5)

    if not registros_processados:
        raise RuntimeError("Erro Crítico: Não foi possível baixar ativos da B3.")

    df_final = pd.concat(registros_processados, ignore_index=True)
    caminho_csv = PROCESSED_DATA_DIR / "mercado_b3.csv"
    df_final.to_csv(caminho_csv, index=False)

    print(f"\nPipeline B3 atualizado com sucesso!")
    print(f"Total de registros consolidados: {len(df_final)}")
    print(f"Colunas geradas: {df_final.columns.tolist()}")
    print(f"Arquivo gerado em: {caminho_csv}")
    return df_final


if __name__ == "__main__":
    executar_pipeline_b3()
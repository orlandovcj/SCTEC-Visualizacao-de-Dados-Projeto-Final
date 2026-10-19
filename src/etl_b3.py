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

# Dicionário de ativos com tickers limpos e setores oficiais
ATIVOS_B3 = {
    "WEGE3.SA": {"ticker": "WEGE3", "setor": "Bens Industriais"},
    "EMBJ3.SA": {"ticker": "EMBJ3", "setor": "Bens Industriais"},
    "VALE3.SA": {"ticker": "VALE3", "setor": "Materiais Básicos"},
    "GGBR4.SA": {"ticker": "GGBR4", "setor": "Materiais Básicos"},
    "KLBN11.SA": {"ticker": "KLBN11", "setor": "Materiais Básicos"},
    "PETR4.SA": {"ticker": "PETR4", "setor": "Petróleo e Gás"},
    "PRIO3.SA": {"ticker": "PRIO3", "setor": "Petróleo e Gás"},
    "EGIE3.SA": {"ticker": "EGIE3", "setor": "Energia Elétrica"},
    "ITUB4.SA": {"ticker": "ITUB4", "setor": "Financeiro"},
    "BBDC4.SA": {"ticker": "BBDC4", "setor": "Financeiro"},
    "ABEV3.SA": {"ticker": "ABEV3", "setor": "Consumo Não Cíclico"},
    "RENT3.SA": {"ticker": "RENT3", "setor": "Consumo Cíclico"}
}

DATA_INICIAL = "2021-01-01"
DATA_FINAL = "2023-12-31"


def obter_sessao_http() -> requests.Session:
    """Cria uma sessão HTTP com cabeçalhos de navegador para contornar bloqueios do Yahoo Finance."""
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
    """Extrai as cotações diárias de um único ativo com tentativas e tratamento de erros."""
    sessao = obter_sessao_http()
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            ativo = yf.Ticker(ticker_sa, session=sessao)
            df = ativo.history(start=inicio, end=fim, auto_adjust=False)
            
            if not df.empty:
                return df
            
            # Tentativa alternativa via método download direto
            df = yf.download(
                tickers=ticker_sa,
                start=inicio,
                end=fim,
                auto_adjust=False,
                progress=False,
                session=sessao
            )
            if not df.empty:
                return df
                
        except Exception as e:
            print(f"Tentativa {tentativa}/{max_tentativas} falhou para {ticker_sa}: {e}")
            time.sleep(1.5)
            
    return pd.DataFrame()


def calcular_indicadores_ativo(df_ativo: pd.DataFrame, ticker: str, setor: str) -> pd.DataFrame:
    """Calcula retorno diário, Base 100, drawdown e volatilidade anualizada."""
    df = df_ativo.copy()
    
    # Padronização de colunas caso venha com MultiIndex de colunas
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.reset_index(inplace=True)
    
    # Tratamento de nome da coluna de data
    col_data = "Date" if "Date" in df.columns else "data"
    df.dropna(subset=["Adj Close", "Close"], inplace=True)
    df.sort_values(by=col_data, inplace=True)
    
    if df.empty:
        return pd.DataFrame()

    df["data"] = pd.to_datetime(df[col_data]).dt.date
    df["ticker"] = ticker
    df["setor"] = setor
    df["preco_fechamento"] = df["Close"].round(2)
    df["preco_ajustado"] = df["Adj Close"].round(4)
    df["volume_financeiro"] = df["Volume"].astype(float)

    # 1. Retorno Diário Simples
    df["retorno_diario"] = df["preco_ajustado"].pct_change()

    # 2. Base 100 (Normalização temporal)
    preco_base = df["preco_ajustado"].iloc[0]
    df["base_100"] = ((df["preco_ajustado"] / preco_base) * 100).round(2)

    # 3. Drawdown Máximo Histórico
    pico = df["preco_ajustado"].cummax()
    df["drawdown"] = (((df["preco_ajustado"] - pico) / pico) * 100).round(2)

    # 4. Volatilidade Móvel Anualizada (Janela 21 dias úteis)
    df["volatilidade_21d"] = (
        df["retorno_diario"].rolling(window=21).std() * np.sqrt(252) * 100
    ).round(2)

    colunas_finais = [
        "data", "ticker", "setor", "preco_fechamento", "preco_ajustado",
        "volume_financeiro", "retorno_diario", "base_100", "drawdown", "volatilidade_21d"
    ]
    return df[colunas_finais]


def executar_pipeline_b3():
    """Executa a coleta serial resiliente de cada ativo e consolida a base."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    registros_processados = []
    print(f"Iniciando coleta resiliente de cotações para {len(ATIVOS_B3)} ativos...")

    for ticker_sa, info in ATIVOS_B3.items():
        ticker_puro = info["ticker"]
        setor = info["setor"]
        print(f"Extraindo dados de {ticker_puro} ({ticker_sa})...")

        df_bruto = extrair_ativo_com_retry(ticker_sa, DATA_INICIAL, DATA_FINAL)
        
        if df_bruto.empty:
            print(f"ALERTA: Não foi possível obter dados para {ticker_sa}.")
            continue

        # Salva backup individual bruto
        df_bruto.to_csv(RAW_DATA_DIR / f"b3_{ticker_puro}_bruto.csv")

        # Processa métricas
        df_tratado = calcular_indicadores_ativo(df_bruto, ticker_puro, setor)
        if not df_tratado.empty:
            registros_processados.append(df_tratado)

        # Intervalo de segurança para respeitar a taxa de requisições da API
        time.sleep(0.5)

    if not registros_processados:
        raise RuntimeError(
            "Erro Crítico: Nenhum ativo da B3 pôde ser baixado via yfinance. "
            "Verifique sua conexão ou restrições de firewall/DNS."
        )

    df_final = pd.concat(registros_processados, ignore_index=True)
    caminho_csv = PROCESSED_DATA_DIR / "mercado_b3.csv"
    df_final.to_csv(caminho_csv, index=False)

    print(f"\nPipeline B3 finalizado com sucesso!")
    print(f"Total de registros consolidados: {len(df_final)}")
    print(f"Ativos processados: {df_final['ticker'].unique().tolist()}")
    print(f"Arquivo gerado em: {caminho_csv}")
    return df_final


if __name__ == "__main__":
    executar_pipeline_b3()
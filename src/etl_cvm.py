"""
Módulo de Extração, Transformação e Carga (ETL) - Demonstrações Contábeis (CVM / DFP)
Projeto: Plataforma Financeira Integrada (Tríade)
Aluno: Orlando Vieira de Castro Junior
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Configuração de diretórios relativos ao projeto
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# Dicionário oficial de mapeamento: CD_CVM -> Metadados do Ativo
COMPANHIAS_CVM = {
    "005410": {"ticker": "WEGE3", "nome": "WEG S.A.", "setor": "Bens Industriais"},
    "020087": {"ticker": "EMBJ3", "nome": "EMBRAER S.A.", "setor": "Bens Industriais"},  # Histórico EMBR3
    "004170": {"ticker": "VALE3", "nome": "VALE S.A.", "setor": "Materiais Básicos"},
    "003980": {"ticker": "GGBR4", "nome": "GERDAU S.A.", "setor": "Materiais Básicos"},
    "012653": {"ticker": "KLBN11", "nome": "KLABIN S.A.", "setor": "Materiais Básicos"},
    "013986": {"ticker": "SUZB3", "nome": "SUZANO S.A.", "setor": "Materiais Básicos"},
    "009512": {"ticker": "PETR4", "nome": "PETROLEO BRASILEIRO S.A. PETROBRAS", "setor": "Petróleo e Gás"},
    "017329": {"ticker": "EGIE3", "nome": "ENGIE BRASIL ENERGIA S.A.", "setor": "Energia Elétrica"},
    "019348": {"ticker": "ITUB4", "nome": "ITAU UNIBANCO HOLDING S.A.", "setor": "Financeiro"},
    "023264": {"ticker": "ABEV3", "nome": "AMBEV S.A.", "setor": "Consumo Não Cíclico"},
    "020575": {"ticker": "JBSS3", "nome": "JBS S.A.", "setor": "Consumo Não Cíclico"},
    "008133": {"ticker": "LREN3", "nome": "LOJAS RENNER S.A.", "setor": "Consumo Cíclico"}
}

ANOS_EXERCICIO = [2019, 2020, 2021, 2022, 2023]


def carregar_e_filtrar_dfp(tipo_dem: str, ano: int) -> pd.DataFrame:
    """Lê o arquivo CSV da DFP para o ano e filtra apenas as 12 companhias de foco."""
    nome_arquivo = f"dfp_cia_aberta_{tipo_dem}_con_{ano}.csv"
    caminho_arquivo = RAW_DATA_DIR / nome_arquivo

    if not caminho_arquivo.exists():
        raise FileNotFoundError(f"Arquivo não localizado em data/raw: {nome_arquivo}")

    # Leitura com tratamento de encoding e separador padrão CVM
    df = pd.read_csv(
        caminho_arquivo,
        sep=";",
        encoding="ISO-8859-1",
        dtype={"CD_CVM": str, "CD_CONTA": str}
    )

    # Filtrar empresas do universo e apenas o último exercício reportado
    df["CD_CVM"] = df["CD_CVM"].str.zfill(6)
    codigos_alvo = list(COMPANHIAS_CVM.keys())
    
    df_filtrado = df[
        (df["CD_CVM"].isin(codigos_alvo)) &
        (df["ORDEM_EXERC"].str.upper() == "ÚLTIMO")
    ].copy()

    # Ajuste de escala monetária (padronizar para Reais inteiros)
    multiplicador = df_filtrado["ESCALA_MOEDA"].apply(
        lambda x: 1000.0 if "MIL" in str(x).upper() else 1.0
    )
    df_filtrado["VL_CONTA_AJUSTADO"] = pd.to_numeric(df_filtrado["VL_CONTA"], errors="coerce") * multiplicador
    df_filtrado["ANO_EXERCICIO"] = ano

    return df_filtrado


def extrair_balancos() -> pd.DataFrame:
    """Consolida os dados de DRE, Ativo e Passivo, calculando os indicadores contábeis."""
    print("Iniciando extração e tratamento dos demonstrativos contábeis da CVM...")
    
    dados_consolidados = []

    for ano in ANOS_EXERCICIO:
        print(f"Processando exercício fiscal de {ano}...")
        df_dre = carregar_e_filtrar_dfp("DRE", ano)
        df_bpa = carregar_e_filtrar_dfp("BPA", ano)
        df_bpp = carregar_e_filtrar_dfp("BPP", ano)

        for cd_cvm, meta in COMPANHIAS_CVM.items():
            ticker = meta["ticker"]
            setor = meta["setor"]
            nome_empresa = meta["nome"]

            # Subconjuntos por empresa
            dre_cia = df_dre[df_dre["CD_CVM"] == cd_cvm]
            bpa_cia = df_bpa[df_bpa["CD_CVM"] == cd_cvm]
            bpp_cia = df_bpp[df_bpp["CD_CVM"] == cd_cvm]

            # Função auxiliar resiliente com fallback por código e descrição
            def obter_valor_conta(df_busca, prefixos_conta, termos_descricao=None):
                """Busca por múltiplos prefixos de conta e, caso não localize, por termo na descrição."""
                if isinstance(prefixos_conta, str):
                    prefixos_conta = [prefixos_conta]

                for prefixo in prefixos_conta:
                    linhas = df_busca[df_busca["CD_CONTA"].str.startswith(prefixo)]
                    if not linhas.empty:
                        return linhas.sort_values(by="CD_CONTA").iloc[0]["VL_CONTA_AJUSTADO"]

                # Fallback semântico pela descrição da conta
                if termos_descricao:
                    for termo in termos_descricao:
                        linhas = df_busca[df_busca["DS_CONTA"].str.upper().str.contains(termo, na=False)]
                        if not linhas.empty:
                            return linhas.sort_values(by="CD_CONTA").iloc[-1]["VL_CONTA_AJUSTADO"]

                return 0.0

            # 1. Contas de DRE
            # Receita Líquida (Industrial: 3.01 | Bancos: 3.01 Receitas de Intermediação Financeira)
            receita_liquida = obter_valor_conta(dre_cia, ["3.01"], ["RECEITA", "INTERMEDIAÇÃO"])
            lucro_bruto = obter_valor_conta(dre_cia, ["3.03"], ["LUCRO BRUTO", "RESULTADO BRUTO"])
            ebit = obter_valor_conta(dre_cia, ["3.05"], ["EBIT", "OPERACIONAL"])
            
            # Lucro Líquido Consolidado:
            # 3.11 para empresas mercantis/industriais; 3.09 para Itaú/financeiras
            lucro_liquido = obter_valor_conta(
                dre_cia, 
                ["3.11", "3.09", "3.99"], 
                ["LUCRO OU PREJUÍZO CONSOLIDADO", "LUCRO LIQUIDO CONSOLIDADO", "LUCRO/PREJUÍZO CONSOLIDADO"]
            )

            # 2. Contas de Balanço Patrimonial
            ativo_total = obter_valor_conta(bpa_cia, ["1"])
            ativo_circulante = obter_valor_conta(bpa_cia, ["1.01"])
            
            # Disponibilidades (Caixa + Aplicações Financeiras)
            caixa_equivalentes = obter_valor_conta(bpa_cia, ["1.01.01"])
            aplicacoes_fin = obter_valor_conta(bpa_cia, ["1.01.02"])
            disponibilidades = caixa_equivalentes + aplicacoes_fin

            passivo_circulante = obter_valor_conta(bpp_cia, ["2.01"])
            
            # Patrimônio Líquido (Conta 2.03 ou 2.07)
            pl = obter_valor_conta(bpp_cia, ["2.03", "2.07"], ["PATRIMÔNIO LÍQUIDO", "PATRIMONIO LIQUIDO"])

            # Empréstimos e Financiamentos (Curto e Longo Prazo)
            divida_cp = obter_valor_conta(bpp_cia, ["2.01.04"])
            divida_lp = obter_valor_conta(bpp_cia, ["2.02.01"])
            divida_bruta = divida_cp + divida_lp
            divida_liquida = divida_bruta - disponibilidades

            # 3. Cálculo de Índices e Indicadores Financeiros
            margem_bruta = (lucro_bruto / receita_liquida * 100) if receita_liquida != 0 else np.nan
            margem_ebit = (ebit / receita_liquida * 100) if receita_liquida != 0 else np.nan
            margem_liquida = (lucro_liquido / receita_liquida * 100) if receita_liquida != 0 else np.nan
            liquidez_corrente = (ativo_circulante / passivo_circulante) if passivo_circulante != 0 else np.nan
            roe = (lucro_liquido / pl * 100) if pl != 0 else np.nan

            dados_consolidados.append({
                "ano": ano,
                "ticker": ticker,
                "cd_cvm": cd_cvm,
                "empresa": nome_empresa,
                "setor": setor,
                "receita_liquida": receita_liquida,
                "lucro_bruto": lucro_bruto,
                "ebit": ebit,
                "lucro_liquido": lucro_liquido,
                "ativo_total": ativo_total,
                "ativo_circulante": ativo_circulante,
                "passivo_circulante": passivo_circulante,
                "patrimonio_liquido": pl,
                "divida_bruta": divida_bruta,
                "disponibilidades": disponibilidades,
                "divida_liquida": divida_liquida,
                "margem_bruta": round(margem_bruta, 2) if pd.notnull(margem_bruta) else np.nan,
                "margem_ebit": round(margem_ebit, 2) if pd.notnull(margem_ebit) else np.nan,
                "margem_liquida": round(margem_liquida, 2) if pd.notnull(margem_liquida) else np.nan,
                "liquidez_corrente": round(liquidez_corrente, 2) if pd.notnull(liquidez_corrente) else np.nan,
                "roe": round(roe, 2) if pd.notnull(roe) else np.nan
            })

    df_resultado = pd.DataFrame(dados_consolidados)
    
    # Exportação tratada com caminho relativo
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    caminho_csv = PROCESSED_DATA_DIR / "balancos_cvm.csv"
    df_resultado.to_csv(caminho_csv, index=False)
    
    print(f"\nPipeline CVM concluído com êxito!")
    print(f"Total de registros gerados: {len(df_resultado)} (12 empresas x 3 exercícios)")
    print(f"Arquivo gravado em: {caminho_csv}")
    return df_resultado


if __name__ == "__main__":
    extrair_balancos()
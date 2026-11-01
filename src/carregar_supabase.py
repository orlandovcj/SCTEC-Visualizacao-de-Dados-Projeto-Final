"""
Módulo de Carga de Dados no PostgreSQL (Supabase)
Projeto: Plataforma Financeira Integrada (Tríade)
Aluno: Orlando Vieira de Castro Junior
"""

from pathlib import Path
import os
import pandas as pd
from sqlalchemy import create_engine
import toml

# Caminhos relativos ao diretório raiz
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
SECRETS_PATH = BASE_DIR / ".streamlit" / "secrets.toml"


def obter_engine_supabase():
    """Recupera as credenciais do secrets.toml e inicializa a engine SQLAlchemy."""
    if not SECRETS_PATH.exists():
        raise FileNotFoundError(
            "Arquivo .streamlit/secrets.toml não localizado. "
            "Crie o arquivo localmente com as credenciais do Supabase."
        )

    secrets = toml.load(SECRETS_PATH)
    cfg = secrets.get("connections", {}).get("postgresql", {})

    if not cfg:
        raise KeyError("Sessão [connections.postgresql] ausente no secrets.toml.")

    usuario = cfg.get("username")
    senha = cfg.get("password")
    host = cfg.get("host")
    porta = cfg.get("port", "5432")
    banco = cfg.get("database", "postgres")

    uri = f"postgresql://{usuario}:{senha}@{host}:{porta}/{banco}"
    return create_engine(uri)


def executar_carga():
    """Carrega as 4 tabelas processadas para o banco de dados no Supabase."""
    print("Conectando ao banco de dados PostgreSQL no Supabase...")
    engine = obter_engine_supabase()

    tabelas = {
        "macro_bacen": PROCESSED_DATA_DIR / "macro_bacen.csv",
        "mercado_b3": PROCESSED_DATA_DIR / "mercado_b3.csv",
        "balancos_cvm": PROCESSED_DATA_DIR / "balancos_cvm.csv",
        "triade_consolidada": PROCESSED_DATA_DIR / "triade_consolidada.csv"
    }

    for nome_tabela, caminho_csv in tabelas.items():
        if not caminho_csv.exists():
            print(f"[ALERTA] Arquivo {caminho_csv.name} não encontrado. Etapa pulada.")
            continue

        print(f"Enviando {caminho_csv.name} para a tabela '{nome_tabela}' no Supabase...")
        df = pd.read_csv(caminho_csv)
        
        # Cria ou substitui as tabelas no esquema público do PostgreSQL
        df.to_sql(nome_tabela, con=engine, if_exists="replace", index=False)
        print(f" -> Tabela '{nome_tabela}' carregada com sucesso ({len(df)} registros).")

    print("\nCarga para o Supabase concluída com êxito!")


if __name__ == "__main__":
    executar_carga()
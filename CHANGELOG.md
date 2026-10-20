# Changelog

Todas as alterações notáveis, entregas de sprint e evoluções arquiteturais deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto adere ao versionamento semântico e boas práticas de GitFlow.

---

## [Não Lançado] - Em Desenvolvimento

### Em Andamento

- **Card 04 / `feature/04-etl-cvm-demonstracoes`**: Implementação do pipeline de extração e tratamento das Demonstrações Financeiras Padronizadas (DFP - CVM) cobrindo os exercícios de 2021 a 2023.

---

## [0.3.0] - 2026-10-20

### Adicionado

- **Pipeline ETL Mercado de Ações (B3)** em `src/etl_b3.py` cobrindo o período de 01/01/2021 a 31/12/2023.
- Mapeamento e ingestão de 12 ativos líquidos da B3 distribuídos em 4 setores estratégicos: Bens Industriais (`WEGE3`, `EMBR3`), Materiais Básicos/Commodities (`VALE3`, `GGBR4`, `KLBN11`), Petróleo/Energia (`PETR4`, `PRIO3`, `EGIE3`) e Consumo/Financeiro (`ITUB4`, `BBDC4`, `ABEV3`, `RENT3`).
- Cálculo padronizado de indicadores financeiros e estatísticos de mercado:
  - Rentabilidade Acumulada Normalizada (**Base 100** com $P_0 = 100$).
  - Retorno diário percentual ($R_t$).
  - **Drawdown Histórico (%)** com rastreamento de topos históricos acumulados.
  - **Volatilidade Móvel Anualizada (%)** em janela de 21 dias úteis ($N = 252$).
- Persistência da base processada em `data/processed/mercado_b3.csv` utilizando caminhos relativos (`pathlib.Path`).
- Gestão ágil: Conclusão do **Card 03** no quadro Kanban do Trello com checklist 100% validada.

### Modificado / Corrigido

- Refatoração da rotina de extração do `yfinance` para execução sequencial resiliente com cabeçalhos HTTP personalizados (`User-Agent` de navegador) e tratamento de tentativas (_retries_ com `time.sleep`), contornando bloqueios de rate limit e respostas vazias do Yahoo Finance.
- Prevenção do erro de concatenação vazia (`ValueError: No objects to concatenate`) por meio de validação prévia de integridade de DataFrames.

---

## [0.2.0] - 2026-10-20

### Adicionado

- **Pipeline ETL Macroeconomia (BACEN / SGS)** em `src/etl_bacen.py` cobrindo o quinquênio de 01/01/2019 a 31/12/2023.
- Integração direta com a API REST pública do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil para extração de 5 séries fundamentais:
  - Série `432`: Taxa Selic Meta (% a.a.).
  - Série `433`: IPCA Variação Mensal (%).
  - Série `13522`: IPCA Acumulado em 12 Meses (%).
  - Série `1`: Taxa de Câmbio Comercial - Dólar PTAX Venda (R$).
  - Série `24364`: Índice de Atividade Econômica do Banco Central (IBC-Br) dessazonalizado.
- Tratamento e harmonização temporal para competência mensal consolidada (último dia útil do mês).
- Cálculo financeiro rigoroso do **Juro Real Ex-Post (% a.a.)** via Equação de Fisher:
  $$r_{\text{real}} = \left( \frac{1 + \frac{\text{Selic}}{100}}{1 + \frac{\text{IPCA}_{12\text{M}}}{100}} - 1 \right) \times 100$$
- Persistência dos dados tratados em `data/processed/macro_bacen.csv`.
- Gestão ágil: Conclusão do **Card 02** no quadro Kanban do Trello.

---

## [0.1.0] - 2026-10-20

### Adicionado

- Estrutura física e lógica inicial do projeto com arquitetura modular:
  - `data/raw/` e `data/processed/` para gestão segura e auditável do ciclo de vida dos dados.
  - `notebooks/` para prototipação e análise exploratória (EDA).
  - `src/` para módulos executáveis de engenharia de dados e cálculos financeiros.
  - `.streamlit/` contendo `config.toml` (estilização corporativa) e `secrets.toml.example` (modelo de credenciais).
  - `app.py` como ponto de entrada da aplicação Streamlit.
  - `README.md` estruturado com o esqueleto oficial dos 14 tópicos obrigatórios do edital.
  - `requirements.txt` com as dependências do ecossistema de dados (`streamlit`, `pandas`, `numpy`, `plotly`, `yfinance`, `requests`, `SQLAlchemy`, `psycopg2-binary`).
- Configuração do GitFlow: criação e fixação das branches `main` e `develop`.
- Gestão ágil: Criação do quadro público oficial no Trello com as colunas `Backlog`, `A Fazer`, `Em Andamento` e `Concluído`, estruturação dos 10 cards do projeto com limites de WIP e conclusão do **Card 01**.

### Segurança

- Configuração rígida do arquivo `.gitignore` para bloquear rastreamento de ambientes virtuais (`.venv/`), credenciais confidenciais (`.streamlit/secrets.toml`), caches (`__pycache__/`) e arquivos brutos pesados.

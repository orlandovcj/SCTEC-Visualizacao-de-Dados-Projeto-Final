# Plataforma Financeira Integrada (Tríade: Macro + Mercado + Balanços)

---

## 1. Título e Resumo Executivo

**Plataforma Financeira Integrada (Tríade: Macro + Mercado + Balanços)**  
Trata-se de uma solução corporativa de Business Intelligence e Data Analytics desenvolvida em Python e Streamlit, cujo objetivo é conectar de ponta a ponta as três forças motrizes da tomada de decisão de investimentos e gestão estratégica: o cenário macroeconômico e a política monetária (BACEN), a precificação e volatilidade dos ativos de capital (B3) e a solidez econômico-financeira contábil das companhias abertas (CVM). A plataforma viabiliza análises multivariadas integradas, substituindo a leitura isolada de balanços ou gráficos de cotações por uma avaliação contextualizada do impacto dos ciclos de juros e câmbio na performance real das empresas brasileiras.

---

## 2. Contexto de Negócio e Pergunta Orientadora

### Contexto

No mercado de capitais e na controladoria corporativa, decisões baseadas em métricas isoladas conduzem a diagnósticos incompletos. O quinquênio 2019–2023 no Brasil foi marcado por volatilidade severa: o choque econômico global de 2020, o corte da taxa Selic à mínima histórica de 2,00% a.a., a posterior escalada inflacionária e o choque de aperto monetário que elevou a taxa básica a 13,75% a.a. Esse ambiente impactou diretamente o custo de capital das empresas, as despesas financeiras corporativas e o valuation em bolsa.

### Problema de Negócio

Qual foi o grau de resiliência das companhias abertas brasileiras frente ao choque monetário (elevação da Selic de 2% para 13,75%) e cambial entre 2021 e 2023, e como a estrutura de custos, o endividamento e a rentabilidade contábil (CVM) explicam as discrepâncias de retorno e risco de mercado (B3) observadas entre os diferentes setores econômicos?

### Perguntas Oficiais Norteadoras do Negócio (Linha 4)

1. **Impacto do Aperto Monetário:** De que maneira o ciclo de aperto monetário da Selic (de 2% para 13,75%) impactou a despesa financeira, alavancagem e o lucro líquido das companhias listadas na CVM?
2. **Sensibilidade Setorial aos Juros:** Como a elevação dos juros e inflação afetou a performance em bolsa (B3) de setores de consumo/varejo vs. setores de energia e bancos?
3. **Proteção Cambial de Commodities:** As empresas exportadoras de commodities apresentaram proteção de margens operacionais e de preço de ação nos momentos de estresse cambial (alta do Dólar PTAX)?
4. **Resiliência Integrada da Carteira:** Qual setor econômico apresentou a melhor relação integrada de resiliência macroeconômica, solidez contábil e retorno em bolsa ao longo do ciclo trienal?

---

## 3. Fonte de Dados e Licença

A aplicação baseia-se exclusivamente em bases de dados públicas e oficiais, auditáveis e com licença aberta governamental/corporativa:

| Domínio                     | Fonte Oficial                                                                   | Recorte Temporal                        | Método de Obtenção                                                                       | Licença / Acesso                                      |
| :-------------------------- | :------------------------------------------------------------------------------ | :-------------------------------------- | :--------------------------------------------------------------------------------------- | :---------------------------------------------------- |
| **Macroeconomia**           | Sistema Gerenciador de Séries Temporais (SGS) - Banco Central do Brasil (BACEN) | 01/01/2019 a 31/12/2023 (5 anos)        | API REST pública oficial via biblioteca `requests` (JSON)                                | Dados Abertos Governamentais (Acesso Público)         |
| **Mercado de Ações**        | Histórico Diário de Cotações da B3 (Brasil, Bolsa, Balcão)                      | 01/01/2021 a 31/12/2023 (3 anos)        | Extração via biblioteca `yfinance` com sessão HTTP estruturada e intervalos de segurança | Dados de Mercado Públicos (Uso Acadêmico/Educacional) |
| **Demonstrações Contábeis** | Portal de Dados Abertos da CVM (Comissão de Valores Mobiliários) - DFP          | Exercícios Fiscais de 2021, 2022 e 2023 | Ingestão e processamento de arquivos CSV consolidados (`_con_`) de DRE, BPA e BPP        | Dados Abertos CVM (Acesso Público Governamental)      |

_Nota de Governança:_ O universo abrange 12 companhias de grande porte distribuídas em setores estratégicos: `WEGE3`, `EMBJ3` (antiga `EMBR3`), `VALE3`, `GGBR4`, `KLBN11`, `SUZB3`, `PETR4`, `EGIE3`, `ITUB4`, `ABEV3`, `JBSS3` e `LREN3`.

---

## 4. Pipeline de Engenharia de Dados (ETL)

O fluxo de dados foi construído de forma modularizada, garantindo independência operacional e reprodutibilidade sem caminhos absolutos:

- **Fontes Públicas e Extração (ETL):**
  - `SGS/BACEN (API REST)` ➔ via `src/etl_bacen.py` ➔ gera `data/processed/macro_bacen.csv`
  - `B3 (Yahoo Finance Engine)` ➔ via `src/etl_b3.py` ➔ gera `data/processed/mercado_b3.csv`
  - `CVM DFP (Portal Abertos)` ➔ via `src/etl_cvm.py` ➔ gera `data/processed/balancos_cvm.csv`
- **Processamento Central:**
  - Os três arquivos CSV acima alimentam o script `src/integracao_triade.py`.
- **Saída Final:**
  - O script consolida os dados e gera o arquivo `data/processed/triade_consolidada.csv`.

### Etapas Executadas:

1. **Extração e Tratamento Macroeconômico (`src/etl_bacen.py`):**
   - Ingestão das séries oficiais: 432 (Selic Meta % a.a.), 433 (IPCA Mensal %), 13522 (IPCA 12M %), 1 (Dólar PTAX Venda R$) e 24364 (IBC-Br dessazonalizado).
   - Harmonização das frequências diárias e mensais para fechamento mensal uniforme (`M`).
   - Cálculo da métrica financeira derivada do **Juro Real Ex-Post (% a.a.)** via Equação de Fisher:  
     $$r_{\text{real}} = \left(\frac{1 + \frac{\text{Selic}}{100}}{1 + \frac{\text{IPCA}_{12\text{M}}}{100}} - 1\right) \times 100$$

2. **Extração e Modelagem de Mercado (`src/etl_b3.py`):**
   - Requisições sequenciais com cabeçalhos HTTP (`User-Agent`) e retries para contornar bloqueios e rate limit da API externa.
   - Cálculo da rentabilidade comparativa normalizada (**Base 100** com $P_0 = 100$).
   - Computação da **Volatilidade Móvel Anualizada (% a.a.)** com janela de 21 pregões úteis ($N = 252$) e do **Drawdown Histórico (%)** frente ao pico histórico acumulado.

3. **Extração e Padronização Contábil (`src/etl_cvm.py`):**
   - Filtro das companhias de foco a partir do código numérico de registro CVM (`CD_CVM`), tratando transições de tickers de mercado (ex.: Embraer sob código CVM `018368`).
   - Ajuste de escala monetária com base na coluna `ESCALA_MOEDA` (multiplicação por 1.000 para valores reportados em 'MIL').
   - Tratamento específico para instituições financeiras (Itaú Unibanco - COSIF/BACEN), cuja DRE consolida o resultado na conta `3.09` (Lucro/Prejuízo Consolidado do Período) em vez da conta industrial padrão `3.11`.
   - Cálculo padronizado dos indicadores contábeis: Margem Bruta, Margem EBIT, Margem Líquida, Liquidez Corrente e Retorno sobre o Patrimônio Líquido (ROE).

---

## 5. Dicionário de Dados

Abaixo estão detalhados os campos consolidados e modelados nas bases tratadas do projeto:

### 5.1. Base Macroeconômica (`data/processed/macro_bacen.csv`)

| Coluna              | Tipo Primitivo | Descrição Financeira / Significado                                | Regra de Cálculo / Origem                                                                   |
| :------------------ | :------------- | :---------------------------------------------------------------- | :------------------------------------------------------------------------------------------ |
| `referencia_mensal` | `datetime`     | Data representativa do último dia da competência mensal analisada | Fechamento mensal da série                                                                  |
| `selic_meta`        | `float`        | Taxa de juros básica da economia definida pelo COPOM (% a.a.)     | SGS Série 432 (último valor do mês)                                                         |
| `ipca_mensal`       | `float`        | Variação percentual mensal do índice oficial de inflação (%)      | SGS Série 433                                                                               |
| `ipca_12m`          | `float`        | Inflação oficial acumulada nos últimos 12 meses (% a.a.)          | SGS Série 13522                                                                             |
| `juro_real_ex_post` | `float`        | Taxa de juros real descontada a inflação observada (% a.a.)       | $\left(\frac{1 + \text{Selic}/100}{1 + \text{IPCA}_{12\text{M}}/100} - 1\right) \times 100$ |
| `dolar_ptax`        | `float`        | Taxa de câmbio comercial de venda do Dólar americano (R$)         | SGS Série 1 (última cotação útil do mês)                                                    |
| `ibc_br`            | `float`        | Índice de Atividade Econômica do Banco Central dessazonalizado    | SGS Série 24364                                                                             |

### 5.2. Base de Mercado de Ações (`data/processed/mercado_b3.csv`)

| Coluna              | Tipo Primitivo | Descrição Financeira / Significado                                       | Regra de Cálculo / Origem                                                       |
| :------------------ | :------------- | :----------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| `data`              | `date`         | Data do pregão útil de negociação                                        | Índice temporal yfinance                                                        |
| `ticker`            | `string`       | Código de negociação da ação na B3 (ex: WEGE3, PETR4)                    | Mapeamento do ativo                                                             |
| `setor`             | `string`       | Classificação setorial de atuação econômica                              | Metadado padronizado do projeto                                                 |
| `preco_fechamento`  | `float`        | Preço nominal de encerramento do pregão (R$)                             | Coluna `Close` da B3                                                            |
| `preco_ajustado`    | `float`        | Preço ajustado por dividendos, juros sobre capital e desdobramentos (R$) | Coluna `Adj Close` da B3                                                        |
| `volume_financeiro` | `float`        | Volume de capital total negociado no pregão (R$)                         | Coluna `Volume` da B3                                                           |
| `retorno_diario`    | `float`        | Variação percentual diária do preço ajustado                             | $\frac{P_t - P_{t-1}}{P_{t-1}}$                                                 |
| `base_100`          | `float`        | Desempenho relativo normalizado (início da série = 100)                  | $\left(\frac{P_t}{P_0}\right) \times 100$                                       |
| `drawdown`          | `float`        | Queda percentual acumulada a partir da máxima histórica até a data (%)   | $\left(\frac{P_t - \max(P_0 \dots P_t)}{\max(P_0 \dots P_t)}\right) \times 100$ |
| `volatilidade_21d`  | `float`        | Risco de mercado móvel anualizado em janela de 21 dias úteis (% a.a.)    | $\text{DesvPad}(R_{21}) \times \sqrt{252} \times 100$                           |

### 5.3. Base de Demonstrações Contábeis (`data/processed/balancos_cvm.csv`)

| Coluna               | Tipo Primitivo | Descrição Financeira / Significado                                   | Regra de Cálculo / Origem                                                        |
| :------------------- | :------------- | :------------------------------------------------------------------- | :------------------------------------------------------------------------------- |
| `ano`                | `integer`      | Ano fiscal de encerramento do exercício social (2021, 2022 ou 2023)  | `ANO_EXERCICIO` da DFP                                                           |
| `ticker`             | `string`       | Ticker de negociação correspondente da companhia                     | Mapeamento corporativo                                                           |
| `cd_cvm`             | `string`       | Código oficial de registro cadastral na CVM (6 dígitos)              | Campo `CD_CVM`                                                                   |
| `empresa`            | `string`       | Razão Social oficial registrada na CVM                               | Metadados da DFP                                                                 |
| `setor`              | `string`       | Segmento econômico consolidado                                       | Mapeamento setorial                                                              |
| `receita_liquida`    | `float`        | Faturamento operacional líquido do exercício (R$)                    | Conta DRE `3.01`                                                                 |
| `lucro_bruto`        | `float`        | Resultado bruto após dedução do custo das vendas/serviços (R$)       | Conta DRE `3.03`                                                                 |
| `ebit`               | `float`        | Lucro operacional antes do resultado financeiro e tributos (R$)      | Conta DRE `3.05`                                                                 |
| `lucro_liquido`      | `float`        | Lucro ou prejuízo líquido consolidado do exercício fiscal (R$)       | Contas DRE `3.11` (Não fin.) e `3.09` (Bancos)                                   |
| `ativo_total`        | `float`        | Valor contábil global dos bens e direitos da companhia (R$)          | Conta BPA `1`                                                                    |
| `ativo_circulante`   | `float`        | Bens e direitos realizáveis no curto prazo até 12 meses (R$)         | Conta BPA `1.01`                                                                 |
| `passivo_circulante` | `float`        | Obrigações e dívidas exigíveis no curto prazo até 12 meses (R$)      | Conta BPP `2.01`                                                                 |
| `patrimonio_liquido` | `float`        | Capital próprio dos acionistas (R$)                                  | Contas BPP `2.03` ou `2.07`                                                      |
| `divida_liquida`     | `float`        | Endividamento oneroso bruto subtraído o caixa disponível (R$)        | $(\text{Passivo Fin. CP} + \text{LP}) - \text{Disponibilidades}$                 |
| `margem_bruta`       | `float`        | Percentual de receita líquida que se converte em lucro bruto (%)     | $\left(\frac{\text{Lucro Bruto}}{\text{Receita Líquida}}\right) \times 100$      |
| `margem_ebit`        | `float`        | Eficiência operacional pura da atividade operacional (%)             | $\left(\frac{\text{EBIT}}{\text{Receita Líquida}}\right) \times 100$             |
| `margem_liquida`     | `float`        | Percentual de receita líquida convertido em lucro aos acionistas (%) | $\left(\frac{\text{Lucro Líquido}}{\text{Receita Líquida}}\right) \times 100$    |
| `liquidez_corrente`  | `float`        | Capacidade de pagamento de curto prazo (múltiplo x)                  | $\frac{\text{Ativo Circulante}}{\text{Passivo Circulante}}$                      |
| `roe`                | `float`        | Retorno gerado sobre o patrimônio líquido dos acionistas (% a.a.)    | $\left(\frac{\text{Lucro Líquido}}{\text{Patrimônio Líquido}}\right) \times 100$ |

---

## 6. Tecnologias e Bibliotecas

A seleção de tecnologias orientou-se pelo equilíbrio entre performance computacional, conformidade metodológica e capacidade analítica corporativa:

- **Python 3.10+:** Linguagem central para engenharia e ciência de dados, oferecendo ampla gama de bibliotecas analíticas e suporte nativo em servidores em nuvem.
- **Pandas:** Utilizado para manipulação matricial, limpeza de tipos primitivos, pivotagem, agrupamentos setoriais e merges relacionais de bases heterogêneas.
- **NumPy:** Empregado nas operações matemáticas vetorizadas (cálculo de raiz quadrada para volatilidade anualizada e logaritmos/potenciações financeiras).
- **Requests:** Responsável pelo consumo seguro e resiliente das APIs públicas do SGS/BACEN, com configuração explícita de timeouts e headers de requisição.
- **yfinance:** Biblioteca especializada para comunicação e extração em lote das séries de cotações diárias e volumes negociados na B3.
- **Plotly Express / Graph Objects:** Ferramenta para construção de visualizações ricas, interativas e com suporte nativo a eixos múltiplos, gráficos de dispersão dimensional e cross-filtering.
- **Streamlit:** Framework para publicação do Data App de Business Intelligence corporativo, permitindo reatividade, gestão de estado via `st.session_state` e cache em memória via `@st.cache_data`.
- **Pathlib / OS:** Emprego estrito de caminhos relativos em todo o projeto, garantindo total portabilidade do código entre sistemas operacionais locais (Windows/Linux/macOS) e o ambiente do Streamlit Cloud.
- **SQLAlchemy & psycopg2-binary:** Drivers para orquestração de conexões estruturadas a bancos de dados relacionais em nuvem (Supabase/PostgreSQL) e rotinas de contingência.

---

## 13. Gestão Ágil e Links do Projeto

- **Quadro Trello:** https://trello.com/invite/b/6ad66e3ec1292230f0ed1436/ATTI89be60e163487560e45b035bc6b248610A1554C7/projeto-final-plataforma-financeira-triade-senai-sc
- **Streamlit Community Cloud:** [Inserir Link Aqui após Deploy]
- **Apresentação em Vídeo:** [Inserir Link Aqui]

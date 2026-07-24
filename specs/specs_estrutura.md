# Financial Data Platform

Uma plataforma de engenharia de dados para ingestão, processamento e disponibilização de dados financeiros utilizando arquitetura em camadas (Landing → Bronze → Silver → Gold), tendo o Google BigQuery como Data Warehouse.

## Arquitetura

```text
                 Financial Modeling Prep
                 Banco Central
                 Outras APIs
                       │
                       ▼
              Pipeline de Ingestão
                       │
                       ▼
                  BigQuery Landing
                       │
                       ▼
                Transformações SQL
        Bronze → Silver → Gold
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
     FastAPI                     Power BI
        │
        ▼
     IA / Aplicações
```

---

# Estrutura do Projeto

```text
financial-data-platform/

│
├── src/
│   │
│   ├── connectors/
│   │      financial_modeling_prep.py
│   │      banco_central.py
│   │      ibge.py
│   │
│   ├── pipelines/
│   │      income_statement_pipeline.py
│   │      balance_sheet_pipeline.py
│   │      cashflow_pipeline.py
│   │      market_pipeline.py
│   │
│   ├── warehouse/
│   │      bigquery_client.py
│   │      sql_executor.py
│   │
│   ├── core/
│   │      config.py
│   │      logger.py
│   │      exceptions.py
│   │
│   ├── services/
│   │      ingestion_service.py
│   │
│   ├── utils/
│   │
│   └── main.py
│
├── sql/
│   │
│   ├── bronze/
│   │      income_statement.sql
│   │      balance_sheet.sql
│   │      cash_flow.sql
│   │      quote.sql
│   │
│   ├── silver/
│   │      dim_company.sql
│   │      dim_date.sql
│   │      fact_income_statement.sql
│   │      fact_balance_sheet.sql
│   │      fact_cash_flow.sql
│   │
│   └── gold/
│          financial_dashboard.sql
│          company_kpis.sql
│          executive_summary.sql
│
├── tests/
│      test_connectors.py
│      test_bigquery.py
│      test_pipelines.py
│
├── docs/
│      architecture.md
│      data_dictionary.md
│      business_rules.md
│
├── .env
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Fluxo do Pipeline

```text
main.py

↓

Extrair dados das APIs

↓

Carregar dados brutos (Landing)

↓

Executar SQL Bronze

↓

Executar SQL Silver

↓

Executar SQL Gold

↓

Finalizar Pipeline
```

---

# Camada de Ingestão

Cada API possui seu próprio conector.

```text
connectors/

FinancialModelingPrep
BancoCentral
IBGE
OpenMeteo
```

Todos os conectores retornam um DataFrame.

Exemplo:

```python
df = FinancialModelingPrep().get_income_statement("MSFT")
```

---

# Camada de Carga

Responsável por enviar qualquer DataFrame para o BigQuery.

```python
loader.upload_dataframe(
    dataframe=df,
    dataset="landing",
    table="income_statement"
)
```

---

# Camadas do Data Warehouse

## Landing

Responsável por armazenar os dados exatamente como vieram da API.

Nenhuma transformação é aplicada.

---

## Bronze

Objetivos:

- Padronização de nomes
- Conversão de tipos
- Remoção de registros inválidos
- Inclusão de data de ingestão
- Auditoria

---

## Silver

Objetivos:

- Aplicação de regras de negócio
- Relacionamentos
- Tratamento de duplicidades
- Normalização
- Enriquecimento

---

## Gold

Objetivos:

- Modelo dimensional
- Tabelas Fato
- Dimensões
- Views analíticas
- Consumo pelo Power BI e APIs

---

# Organização do BigQuery

```text
financial_analytics

├── landing
│      income_statement
│      balance_sheet
│      cash_flow
│      company_profile
│      quote
│
├── bronze
│
├── silver
│
└── gold
```

---

# Execução das Transformações

Todo o processamento acontece através de SQL.

```text
Landing

↓

Bronze

↓

Silver

↓

Gold
```

O Python apenas executa os scripts SQL.

---

# Configuração

Arquivo `.env`

```env
PROJECT_ID=financial-analytics

DATASET_LANDING=landing
DATASET_BRONZE=bronze
DATASET_SILVER=silver
DATASET_GOLD=gold

FMP_API_KEY=

GOOGLE_APPLICATION_CREDENTIALS=
```

---

# Logs

Cada execução gera logs estruturados.

Exemplo:

```text
2026-07-23 14:00:01 INFO Iniciando pipeline

2026-07-23 14:00:02 INFO Extraindo Income Statement

2026-07-23 14:00:03 INFO 125 registros encontrados

2026-07-23 14:00:04 INFO Carga Landing concluída

2026-07-23 14:00:06 INFO Bronze concluído

2026-07-23 14:00:08 INFO Silver concluído

2026-07-23 14:00:10 INFO Gold concluído

2026-07-23 14:00:10 INFO Pipeline finalizado
```

---

# Tratamento de Erros

Fluxo de exceções.

```text
Erro na API

↓

Retry

↓

Falhou novamente

↓

Registrar Log

↓

Encerrar Pipeline
```

---

# Testes

Cobertura mínima:

- API respondeu corretamente
- DataFrame não está vazio
- Colunas obrigatórias existem
- Carga para o BigQuery executada
- SQL executado sem erros

---

# Roadmap

## Fase 1

- [ ] Financial Modeling Prep
- [ ] BigQuery
- [ ] Landing
- [ ] Bronze
- [ ] Silver
- [ ] Gold

## Fase 2

- [ ] Banco Central
- [ ] IBGE
- [ ] OpenMeteo

## Fase 3

- [ ] FastAPI

## Fase 4

- [ ] Docker

## Fase 5

- [ ] GitHub Actions

## Fase 6

- [ ] Testes Automatizados

## Fase 7

- [ ] IA Generativa

---

# Stack Tecnológica

- Python
- Google BigQuery
- SQL
- Pandas
- Requests
- python-dotenv
- Google Cloud SDK
- FastAPI
- Docker
- GitHub Actions
- Power BI
- OpenAI API (futuro)

---

# Objetivo

Construir uma plataforma de engenharia de dados escalável, modular e desacoplada para ingestão de dados financeiros, seguindo boas práticas de arquitetura corporativa e disponibilizando uma camada Gold pronta para consumo por aplicações analíticas, APIs e ferramentas de Business Intelligence.
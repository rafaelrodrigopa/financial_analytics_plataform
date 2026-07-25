# Financial Analytics Platform 🚀

Uma plataforma completa de **Engenharia de Dados** e **Analytics Engineering** desenvolvida para ingestão, processamento, higienização e modelagem dimensional de dados financeiros de empresas de capital aberto (Financial Modeling Prep API), utilizando a **Arquitetura Medallion** no **Google BigQuery** e orquestração via **Dataform**.

---

## 🏗️ Arquitetura do Pipeline

O pipeline segue rigorosamente a **Arquitetura Medallion** dividida em 4 camadas de dados e otimizada com o Dataform para governança e transformação SQL:

```text
┌─────────────────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  API FMP / Financial    │ ──> │ Landing Zone │ ──> │ Bronze Layer │ ──> │ Silver Layer │ ──> │ Gold Layer  │
│  Modeling Prep          │     │ (Raw Staged) │     │ (Raw Historic│     │ (Clean Data) │     │ (Analytics) │
└─────────────────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
                                                                                 │                    │
                                                                                 ▼                    ▼
                                                                            Dataform Core      Data Marts & BI
```

### 🧱 Datasets no BigQuery
- **`landing`**: Zona de staging bruta para armazenamento temporário dos payloads JSON consumidos das APIs.
- **`bronze`**: Armazenamento bruto persistente e histórico com auditoria e controle de ingestão.
- **`silver`**: Dados limpos, desduplicados, tipados e higienizados via Dataform SQLX.
- **`gold`**: Camada analítica dimensional com tabelas fato, dimensões, indicadores financeiros, métricas temporais e **Data Marts desnormalizados** para consumo direto no Power BI e Looker Studio.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.12+
- **Analytics Engineering**: Dataform Core (v3.0.0) / Node.js
- **Data Warehouse**: Google BigQuery
- **Bibliotecas Python**: `google-cloud-bigquery`, `pandas-gbq`, `pyarrow`, `python-dotenv`, `pydantic`
- **Qualidade de Dados**: Dataform Assertions (32 testes automatizados)

---

## 📂 Estrutura do Repositório

```text
financial-analytics-platform/
│
├── definitions/                        # Definições SQLX do Dataform
│   ├── sources/                        # Declaração das fontes de dados Bronze
│   ├── silver/                         # Modelos de staging da camada Silver
│   │   └── assertions/                 # Testes de integridade da camada Silver
│   └── gold/                           # Modelos dimensionais da camada Gold
│       ├── dimensions/                 # dim_company.sqlx, dim_date.sqlx
│       ├── facts/                      # fact_financial_statements, fact_daily_quotes, fact_financial_ratios
│       ├── marts/                      # dm_financial_valuation.sqlx (Data Marts)
│       └── assertions/                 # Assertions de validação de valores, chaves FK e integridade
│
├── includes/                           # Módulos JS reutilizáveis para Dataform (audit_fields.js)
├── docs/                               # Planos de arquitetura, melhorias e documentação técnica
│
├── src/                                # Código Python de Ingestão e Conectores
│   ├── connectors/                     # Conector FMP API
│   ├── core/                           # Gerenciador de configurações de ambiente
│   ├── schemas/                        # Schemas Pydantic / dataclasses
│   ├── services/                       # IngestionService e BronzeService
│   └── warehouse/                      # Cliente de abstração do BigQuery
│
├── tests/                              # Suíte de testes Python e conexão
│
├── .env.example                        # Modelo de variáveis de ambiente Python
├── .df-credentials.json.example        # Modelo de credenciais do Dataform CLI
├── workflow_settings.yaml              # Configuração do projeto Dataform Core
├── requirements.txt                    # Dependências Python
└── README.md                           # Documentação oficial do repositório
```

---

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:
1. **Python 3.12** ou superior.
2. **Node.js** (v18+) e `npm` / `npx`.
3. Uma conta ativa no **Google Cloud Platform (GCP)** com o **BigQuery** habilitado.
4. Uma chave de API gratuita ou paga da **[Financial Modeling Prep (FMP)](https://financialmodelingprep.com/)**.

---

## 🚀 Como Configurar e Executar Passo a Passo

### 1. Clonar o Repositório
```bash
git clone https://github.com/rafaelrodrigopa/financial_analytics_plataform.git
cd financial-analytics-platform
```

### 2. Criar e Ativar o Ambiente Virtual Python
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\activate

# Linux / MacOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as Dependências Python
```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente (`.env`)
Crie um arquivo `.env` na raiz do projeto copiando o modelo `.env.example`:

```env
# Google BigQuery & GCP
GOOGLE_APPLICATION_CREDENTIALS=credenciais/chave_conta_servico.json
GCP_PROJECT_ID=seu-gcp-project-id

# Financial Modeling Prep API
FMP_API_KEY=sua_fmp_api_key_aqui

# Datasets no BigQuery
BQ_DATASET_LANDING=landing
BQ_DATASET_BRONZE=bronze
BQ_DATASET_SILVER=silver
BQ_DATASET_GOLD=gold
```

### 5. Configurar as Credenciais no Projeto
1. Salve o arquivo JSON da sua Service Account do GCP no caminho `credenciais/chave_conta_servico.json`. Assegure-se que a conta possui o papel de **BigQuery Admin** ou **BigQuery Data Editor / Job User**.
2. Crie o arquivo `.df-credentials.json` na raiz do projeto para autenticação do **Dataform CLI**:

```json
{
  "projectId": "seu-gcp-project-id",
  "location": "US",
  "credentials": "{\n  \"type\": \"service_account\",\n  \"project_id\": \"seu-gcp-project-id\",\n  \"private_key_id\": \"...\",\n  \"private_key\": \"...\",\n  \"client_email\": \"...\"\n}"
}
```

> ⚠️ **Segurança**: Nunca envie os arquivos `.env`, `.df-credentials.json` ou chaves de conta de serviço `.json` para o Git. Todos já estão protegidos no `.gitignore`.

---

## 🔄 Executando o Pipeline Completo

### Passo A: Testar a Conexão com o BigQuery
```bash
python tests/test_bigquery_connection.py
```
*Saída esperada: Listagem dos datasets `landing`, `bronze`, `silver` e `gold`.*

### Passo B: Executar a Ingestão de Dados (Landing & Bronze)
Execute o pipeline Python para extrair os demonstrativos financeiros e cotações das APIs e carregar nas camadas Landing e Bronze:
```bash
python -c "from src.services.bronze_service import BronzeService; BronzeService().run_full_bronze_pipeline()"
```

### Passo C: Executar as Transformações com o Dataform (Silver & Gold)

#### 1. Instalar os pacotes e dependências do Dataform
```bash
npx @dataform/cli install
```

#### 2. Compilar o projeto Dataform
Valida a sintaxe SQLX e compila o Grafo de Dependências (DAG) com 41+ ações e 32+ assertions:
```bash
npx @dataform/cli compile
```

#### 3. Executar e Materializar todas as tabelas e testar Assertions no BigQuery
```bash
npx @dataform/cli run
```

#### 4. (Opcional) Executar apenas a camada Gold
```bash
npx @dataform/cli run --tags gold
```

---

## 🤖 Automação e Agendamento da Ingestão na Landing Zone

Você pode escolher entre duas estratégias avançadas de automação para executar a ingestão diária sem necessidade de intervenção manual:

### Opção A: Automação via GitHub Actions

Para automatizar a execução diária usando o GitHub Actions, crie o arquivo `.github/workflows/daily_ingestion.yml` com a seguinte estrutura:

```yaml
name: Daily Financial Ingestion Pipeline

on:
  schedule:
    - cron: '0 3 * * *' # Executa diariamente às 00:00 Horário de Brasília
  workflow_dispatch:

jobs:
  run-ingestion:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - env:
          GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
          FMP_API_KEY: ${{ secrets.FMP_API_KEY }}
          GOOGLE_APPLICATION_CREDENTIALS: credenciais/chave_conta_servico.json
        run: |
          mkdir -p credenciais
          echo "${{ secrets.GCP_SA_KEY }}" > credenciais/chave_conta_servico.json
          python -c "from src.services.bronze_service import BronzeService; BronzeService().run_full_bronze_pipeline()"
```

#### Como Configurar os Secrets no GitHub:
1. No seu repositório GitHub, navegue até **Settings** > **Secrets and variables** > **Actions**.
2. Clique em **New repository secret** e cadastre as variáveis de ambiente:
   - **`GCP_PROJECT_ID`**: ID do seu projeto no Google Cloud (ex: `seu-projeto-gcp`).
   - **`FMP_API_KEY`**: Sua chave de API da Financial Modeling Prep.
   - **`GCP_SA_KEY`**: O conteúdo do arquivo JSON da sua Service Account do GCP.

---

### Opção B: Automação 100% Serverless no GCP (Cloud Scheduler + Cloud Run Job)

Se você preferir manter toda a orquestração dentro da infraestrutura do próprio Google Cloud Platform (GCP):

#### 1. Construir e publicar a imagem Docker da aplicação no Artifact Registry
```bash
# Autenticar a CLI do gcloud com o Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Construir a imagem Docker
docker build -t us-central1-docker.pkg.dev/seu-projeto-gcp/financial-repo/ingestion-app:latest .

# Enviar a imagem para o Artifact Registry do GCP
docker push us-central1-docker.pkg.dev/seu-projeto-gcp/financial-repo/ingestion-app:latest
```

#### 2. Criar o Cloud Run Job
```bash
gcloud run jobs create daily-ingestion-job \
    --image us-central1-docker.pkg.dev/seu-projeto-gcp/financial-repo/ingestion-app:latest \
    --region us-central1 \
    --set-env-vars GCP_PROJECT_ID=seu-projeto-gcp,FMP_API_KEY=sua_chave,BQ_DATASET_LANDING=landing,BQ_DATASET_BRONZE=bronze \
    --service-account financial-platform@seu-projeto-gcp.iam.gserviceaccount.com
```

#### 3. Agendar a Execução Diária via GCP Cloud Scheduler
Crie o agendador no **Cloud Scheduler** para disparar o Cloud Run Job via requisição HTTP autenticada:
```bash
gcloud scheduler jobs create http daily-ingestion-schedule \
    --location us-central1 \
    --schedule "0 0 * * *" \
    --time-zone "America/Sao_Paulo" \
    --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/seu-projeto-gcp/jobs/daily-ingestion-job:run" \
    --http-method POST \
    --oauth-service-account-email financial-platform@seu-projeto-gcp.iam.gserviceaccount.com
```

---

## 📊 Estrutura e Tabelas da Camada Gold

A camada Gold disponibiliza a seguinte estrutura dimensional pronta para consumo por Business Intelligence:

| Tabela / Data Mart | Tipo | Descrição |
| :--- | :--- | :--- |
| **`gold.dm_financial_valuation`** | Data Mart | **Visão Wide de Valuation**: Unifica cotações em tempo real, demonstrativos, indicadores de rentabilidade, múltiplos (P/L, P/VP, P/S, FCF Yield, EV/EBIT), crescimento (YoY/QoQ) e flags de governança. |
| **`gold.fact_financial_statements`** | Tabela Fato | DRE, Balanço Patrimonial e Fluxo de Caixa unificados em português com flags de prejuízo, patrimônio negativo e caixa líquido. |
| **`gold.fact_financial_ratios`** | Tabela Fato | Indicadores e margens financeiras (%), além de métricas de crescimento de receita e lucro YoY e QoQ. |
| **`gold.fact_daily_quotes`** | Tabela Fato | Cotações diárias e métricas de preço e volume traduzidas para o português. |
| **`gold.dim_company`** | Dimensão | Cadastro oficial de empresas listadas na bolsa em português. |
| **`gold.dim_date`** | Dimensão | Calendário temporal para inteligência temporal no Power BI e Looker Studio. |

---

## 💡 Nota Arquitetural sobre o BigQuery Free Tier (Sandbox) & Atualização Incremental em Produção

### 1. Por que o projeto utiliza `type: "table"` no ambiente de testes?
No **BigQuery Sandbox (Free Tier / Plano Gratuito do GCP)**, o Google bloqueia intencionalmente comandos DML (`MERGE`, `INSERT INTO`, `DELETE`).
Como o Dataform traduz a materialização `type: "incremental"` em instruções SQL DML (`MERGE INTO` / `INSERT INTO`), tentar rodar em modo incremental no Sandbox resultaria no erro de permissão `403 Forbidden: DML queries are not supported in the free tier`.

Por esta razão, todos os modelos do projeto utilizam `type: "table"` (que gera o comando DDL `CREATE OR REPLACE TABLE`), garantindo execução 100% livre de erros e alta performance no plano gratuito.

---

### 2. Passo a Passo para Ativar Carga Incremental (`type: "incremental"`) em Produção

Caso você migre a sua conta do GCP para o modo de produção (com conta de faturamento/billing ativada), siga este passo a passo para alterar as tabelas fatos para a estratégia incremental de alta performance:

#### Passo 1: Alterar a propriedade `type` nos arquivos SQLX
Altere de `type: "table"` para `type: "incremental"` nos seguintes arquivos de dados diários e periódicos:
- `definitions/silver/stg_quote.sqlx`
- `definitions/gold/facts/fact_daily_quotes.sqlx`
- `definitions/gold/facts/fact_financial_statements.sqlx`
- `definitions/gold/facts/fact_financial_ratios.sqlx`

#### Passo 2: Adicionar a cláusula `${when(incremental(), ...)}` na instrução SQLX
Adicione a condição de novidade ao final da consulta SQL de cada modelo para processar apenas os novos registros ingeridos:

```sql
config {
  type: "incremental",
  schema: "gold",
  name: "fact_daily_quotes",
  bigquery: {
    partitionBy: "data_ingestao",
    clusterBy: ["codigo_ativo"]
  }
}

SELECT
  symbol AS codigo_ativo,
  price AS preco_atual,
  change_percent AS variacao_percentual,
  change_amount AS variacao_nominal,
  day_low AS preco_minimo_dia,
  day_high AS preco_maximo_dia,
  year_high AS preco_maximo_52sem,
  year_low AS preco_minimo_52sem,
  market_cap AS valor_mercado,
  volume AS volume_negociado,
  DATE(_ingested_at) AS data_ingestao,
  _ingested_at
FROM
  ${ref("stg_quote")}
${when(incremental(), `WHERE _ingested_at > (SELECT MAX(_ingested_at) FROM ${self()})`)}
```

#### Passo 3: Recompilar e Executar via Dataform CLI
```bash
# 1. Compilar para validar o novo DAG incremental
npx @dataform/cli compile

# 2. Executar a carga incremental em produção
npx @dataform/cli run

# 3. (Caso precise forçar o recálculo total da tabela incremental)
npx @dataform/cli run --full-refresh
```

---

## 📝 Licença

Este projeto é disponibilizado sob a licença MIT. Sinta-se à vontade para utilizar, modificar e contribuir!


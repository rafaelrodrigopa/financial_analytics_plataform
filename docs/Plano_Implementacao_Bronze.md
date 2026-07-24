# Plano de Implementação: Camada Bronze & Integração Dataform

Documentação técnica completa do plano de implementação da **Camada Bronze** e integração com o **Dataform** na **Financial Analytics Platform**, utilizando a **Arquitetura Medallion** no **Google BigQuery**.

---

## 1. Visão Geral da Arquitetura

O pipeline segue a Arquitetura Medallion para transformar dados brutos consumidos da API da Financial Modeling Prep em modelos analíticos otimizados:

```text
┌─────────────────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  API FMP / Financial    │ ──> │ Landing Zone │ ──> │ Bronze Layer │ ──> │ Silver Layer │ ──> │ Gold Layer  │
│  Modeling Prep (Python) │     │ (Staging Raw)│     │ (Raw Historic│     │ (Clean Data) │     │ (Analytics) │
└─────────────────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
                                                      ▲                    ▲
                                                      │                    │
                                                Python/BQ Jobs       Dataform (ELT)
```

---

## 2. O Papel do Dataform na Arquitetura

* **Ingestão (Landing → Bronze)**: Executada via **Python** (`IngestionService` e `BronzeService`), que realiza chamadas HTTP à API, trata throttling/retries, valida contratos via `Pydantic` e persiste os registros com metadados no BigQuery.
* **Transformação (Bronze → Silver → Gold)**: Executada via **Dataform (ELT)**. O Dataform opera diretamente dentro do BigQuery executando modelos SQLX para limpeza, deduplicação, tipagem e criação de tabelas fato e dimensão.

---

## 3. Diretrizes e Boas Práticas da Camada Bronze

1. **Abordagem Append-Only (Imutabilidade)**:
   - A camada Bronze preserva o histórico exato de todas as ingestões. Registros não são sobrescritos ou alterados nesta camada.
2. **Metadados de Auditoria Obligatórios**:
   - Cada registro inserido na Bronze recebe:
     - `_ingested_at` (`TIMESTAMP` UTC da carga)
     - `_source` (`STRING` indicando a origem/endpoint)
     - `_execution_id` (`STRING` UUID único da execução)
3. **Particionamento e Clusterização no BigQuery**:
   - **Particionamento**: `DATE(_ingested_at)` para minimizar custos de escaneamento de dados nas consultas diárias.
   - **Clusterização**: `symbol` (ticker da empresa, ex: `AAPL`, `PETR4`) e `period` (`FY`, `Q1`, etc.).

---

## 4. Tabelas Escopadas para a Camada Bronze

| Tabela Bronze | Dataset BigQuery | Origem (API FMP) | Chaves de Clusterização |
| :--- | :--- | :--- | :--- |
| `fmp_balance_sheet` | `bronze` | Balance Sheet Statement | `symbol`, `calendarYear` |
| `fmp_income_statement` | `bronze` | Income Statement | `symbol`, `calendarYear` |
| `fmp_cash_flow` | `bronze` | Cash Flow Statement | `symbol`, `calendarYear` |
| `fmp_financial_ratios` | `bronze` | Financial Ratios | `symbol`, `date` |
| `fmp_key_metrics` | `bronze` | Key Metrics | `symbol`, `date` |

---

## 5. Etapas Detalhadas de Implementação

### 📌 Etapa 1: Construção do Serviço `BronzeService` (Python)
- **Arquivo**: `src/services/bronze_service.py`
- **Responsabilidades**:
  - Interagir com o `BigQueryClient` para garantir a criação automatizada das tabelas na `bronze`.
  - Aplicar o esquema com particionamento nativo em `_ingested_at` e clusterização por `symbol`.
  - Adicionar campos auditáveis e realizar inserção idempotente em lote (`WRITE_APPEND`).

### 📌 Etapa 2: Módulo de Testes de Integração
- **Arquivo**: `tests/test_bronze_layer.py`
- **Validações**:
  - Testar a conexão e criação de tabelas no dataset `bronze`.
  - Simular ingestão e verificar se os metadados `_ingested_at`, `_source` e `_execution_id` foram gravados corretamente.
  - Validar a partição de datas e integridade do payload.

### 📌 Etapa 3: Inicialização da Estrutura do Dataform
- **Diretório**: `definitions/`
- **Arquivos**:
  - `definitions/dataform.json`: Configuração do projeto Dataform.
  - `definitions/sources/bronze_sources.js`: Declaração das tabelas do dataset `bronze` como fontes oficiais.
  - `definitions/silver/stg_balance_sheet.sqlx`: Primeiro modelo de transformação Bronze → Silver.

---

## 6. Plano de Verificação e Validação

### Testes Automatizados
```powershell
# Ativar ambiente virtual
.\.venv\Scripts\activate

# Executar testes da camada Bronze
python -m unittest tests/test_bronze_layer.py

# Verificar qualidade do código
python -m .venv\Scripts\ruff check .
```

### Validação no Console GCP / BigQuery
- Consultar a tabela via SQL no BigQuery para conferir partições:
  ```sql
  SELECT table_name, partition_id, total_rows
  FROM `civil-glyph-503402-c9.bronze.INFORMATION_SCHEMA.PARTITIONS`
  WHERE table_name = 'fmp_balance_sheet';
  ```

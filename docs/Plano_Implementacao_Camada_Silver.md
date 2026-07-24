# Plano de Implementação: Camada Silver (Dataform & Data Quality)

Documentação técnica completa do plano de implementação da **Camada Silver** na **Financial Analytics Platform**, utilizando a ferramenta nativa **Dataform** no **Google BigQuery** para desduplicação, limpeza, padronização de esquemas e testes automatizados de qualidade de dados (*Assertions*).

---

## 1. Visão Geral da Arquitetura Silver

A Camada Silver é a camada de **Dados Limpos e Padronizados (Clean Data)**. Ela transforma os dados brutos e históricos da camada **Bronze** em tabelas otimizadas, desduplicadas, com tipagem forte e testes de integridade declarativos.

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

## 2. Pilares de Transformação da Camada Silver

1. **Deduplicação Inteligente (Window Functions)**:
   - Aplicação de `QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol, date, period ORDER BY _ingested_at DESC) = 1` para garantir que apenas o último snapshot histórico seja mantido.
2. **Tipagem Rígida e Padronização de Nulos**:
   - Conversão de strings de data para `DATE`.
   - Casting de valores monetários para `NUMERIC` / `FLOAT64`.
   - Substituição de valores inválidos ou zerados por `NULL` quando aplicável.
3. **Dataform Assertions (Testes de Qualidade Nativos)**:
   - **Unicidade de Chave Primária**: `uniqueKey: ["symbol", "date", "period"]`.
   - **Validação de Não Nulos**: `nonNull: ["symbol", "date"]`.
   - **Regras de Negócio Financeiras**: Assertions personalizadas (ex: `totalAssets >= 0`).
4. **Preservação Semiestruturada**:
   - Manutenção da coluna `_raw_payload` (tipo `JSON`) para permitir extrações retroativas sem quebrar modelos em produção.

---

## 3. Mapeamento dos Modelos Dataform na Silver

| Tabela Silver | Modelo SQLX | Tabela Origem (Bronze) | Chave Primária Única |
| :--- | :--- | :--- | :--- |
| `silver.stg_balance_sheet` | `definitions/silver/stg_balance_sheet.sqlx` | `bronze.fmp_balance_sheet` | `symbol`, `date`, `period` |
| `silver.stg_income_statement` | `definitions/silver/stg_income_statement.sqlx` | `bronze.fmp_income_statement` | `symbol`, `date`, `period` |
| `silver.stg_cash_flow` | `definitions/silver/stg_cash_flow.sqlx` | `bronze.fmp_cash_flow` | `symbol`, `date`, `period` |
| `silver.dim_company_profile` | `definitions/silver/dim_company_profile.sqlx` | `bronze.fmp_company_profile` | `symbol` |
| `silver.stg_quote` | `definitions/silver/stg_quote.sqlx` | `bronze.fmp_quote` | `symbol`, `_ingested_at` |

---

## 4. Etapas Detalhadas de Implementação

### 📌 Etapa 1: Inicialização da Estrutura do Dataform
- Criar a estrutura do projeto Dataform no repositório:
  - `definitions/dataform.json`: Configurações globais do projeto (`defaultSchema`: `silver`).
  - `definitions/sources/bronze_sources.js`: Declarações de origem das tabelas da Bronze.

### 📌 Etapa 2: Desenvolvimento dos Modelos SQLX na Silver
- Desenvolver os modelos de staging em SQLX para Balance Sheet, Income Statement, Cash Flow, Company Profile e Quote.
- Adicionar definições de `config` (tipo `table` ou `incremental`, particionamento por `date` e clusterização por `symbol`).

### 📌 Etapa 3: Implementação das Assertions de Qualidade
- Criar testes de validação de não-nulos e unicidade em cada modelo SQLX.
- Adicionar testes SQLX customizados para regras de negócio (ex: integridade do balanço patrimonial `totalAssets = totalLiabilities + totalStockholdersEquity`).

### 📌 Etapa 4: Compilação e Execução de Testes
- Compilar o grafo de dependências DAG e executar a compilação do Dataform no projeto GCP `civil-glyph-503402-c9`.

---

## 5. Plano de Verificação e Validação

### Compilação via Dataform CLI
```powershell
# Compilar projeto Dataform
npx @dataform/cli compile

# Executar transformações no BigQuery
npx @dataform/cli run --project civil-glyph-503402-c9
```

### Consultas SQL de Validação no BigQuery
- Teste de ausência de duplicatas:
  ```sql
  SELECT symbol, date, period, COUNT(1)
  FROM `civil-glyph-503402-c9.silver.stg_balance_sheet`
  GROUP BY 1, 2, 3
  HAVING COUNT(1) > 1;
  ```

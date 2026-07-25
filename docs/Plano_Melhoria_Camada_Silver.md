# Plano de Melhorias e Boas Práticas: Camada Silver (Dataform & Data Engineering)

Documentação técnica do plano de otimização, governança e refatoração da **Camada Silver** na **Financial Analytics Platform**, utilizando recursos avançados do **Dataform** no **Google BigQuery**.

---

## 1. Visão Geral do Plano de Melhorias

Com a conclusão da estrutura inicial da Camada Silver (tabelas desduplicadas e 15 assertions de qualidade aprovadas), este plano estabelece as diretrizes para elevar a arquitetura a um nível de **Engenharia de Dados Sênior**, focando em:
1. **Governança de Dados & Dicionário Integrado** (BigQuery Data Catalog).
2. **Eficiência de Custos e Performance** (Materialização Incremental no Dataform).
3. **Qualidade e Sanitização de Dados** (Tratamento rigoroso de strings e nulos).
4. **Manutenibilidade de Código (DRY)** (Módulos JavaScript reusáveis).
5. **Orquestração Granular** (Tags de execução seletiva por frequência de ingestão).

---

## 2. Pilares de Otimização e Detalhamento Técnico

### 📌 Melhoria 1: Documentação no Nível de Coluna (`columns`)
* **Descrição**: Adicionar o dicionário de dados completo no bloco `config { columns: { ... } }` de cada arquivo SQLX.
* **Benefício**: Sincronização automática com o **BigQuery Data Catalog**, disponibilizando a documentação de cada atributo diretamente para analistas de BI no PowerBI / Looker Studio.
* **Modelos Afetados**:
  * `definitions/silver/stg_balance_sheet.sqlx`
  * `definitions/silver/stg_income_statement.sqlx`
  * `definitions/silver/stg_cash_flow.sqlx`
  * `definitions/silver/stg_quote.sqlx`
  * `definitions/silver/dim_company_profile.sqlx`

### 📌 Melhoria 2: Materialização Incremental para Cotações (`stg_quote.sqlx`)
* **Descrição**: Alterar o tipo de materialização de `type: "table"` para `type: "incremental"` em cotações.
* **Lógica SQLX**:
  ```sql
  config {
    type: "incremental",
    bigquery: {
      partitionBy: "DATE(_ingested_at)",
      clusterBy: ["symbol"]
    }
  }

  SELECT ...
  FROM ${ref("fmp_quote")}
  ${when(incremental(), `WHERE _ingested_at > (SELECT MAX(_ingested_at) FROM ${self()})`)}
  QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol, DATE(_ingested_at) ORDER BY _ingested_at DESC) = 1
  ```
* **Benefício**: Redução drástica no volume de dados varridos no BigQuery durante atualizações contínuas de cotação em tempo real.

> [!NOTE]
> **Observação Arquitetural sobre o BigQuery Sandbox (Free Tier)**:
> O BigQuery na camada gratuita (*Free Tier Sandbox* sem conta de faturamento ativada) bloqueia instruções **DML (`INSERT INTO`, `UPDATE`, `MERGE`)**. Como a materialização `type: "incremental"` do Dataform traduz as cargas em comandos `INSERT INTO`, ela requer um projeto com Billing ativado. No ambiente Sandbox gratuito, os modelos devem ser mantidos como `type: "table"` (que utilizam `CREATE OR REPLACE TABLE`), garantindo 100% de compatibilidade e execução sem erros.

### 📌 Melhoria 3: Higienização Avançada de Strings (`UPPER`, `TRIM`, `NULLIF`)
* **Descrição**: Aplicar funções de sanitização para evitar inconsistências sutis decorrentes de espaços extras ou strings vazias enviadas pela API.
* **Regras**:
  * `UPPER(TRIM(symbol))` para símbolos de ativos (`AAPL`, `MSFT`).
  * `NULLIF(TRIM(period), '')` para transformar strings em branco (`""`) em `NULL` real.
  * `UPPER(TRIM(currency))` e `UPPER(TRIM(exchange))`.

### 📌 Melhoria 4: Módulos JavaScript para Reutilização de Código (`includes/`)
* **Descrição**: Criar utilitários JavaScript no diretório `definitions/includes/` para padronizar seleções repetitivas.
* **Arquivos a Criar**:
  * `definitions/includes/audit_fields.js`: Função auxiliar que gera a seleção padronizada dos campos de auditoria (`_ingested_at`, `_source`, `_execution_id`, `_row_hash`, `_raw_payload`).

### 📌 Melhoria 5: Orquestração Seletiva com Tags Granulares
* **Descrição**: Categorizar os modelos SQLX com tags por frequência de atualização para orquestração otimizada no Airflow / Cloud Composer ou Dataform Workflows.
* **Mapeamento de Tags**:
  * `tags: ["silver", "intraday"]` -> `stg_quote.sqlx`
  * `tags: ["silver", "financial_statements", "quarterly"]` -> `stg_balance_sheet.sqlx`, `stg_income_statement.sqlx`, `stg_cash_flow.sqlx`
  * `tags: ["silver", "dimensions", "daily"]` -> `dim_company_profile.sqlx`

---

## 3. Plano de Execução e Validação

1. **Implementação dos Módulos JavaScript (`includes/ audit_fields.js`)**.
2. **Atualização dos Modelos SQLX na Silver** com `columns`, sanitização de strings, tags granulares e estratégia incremental em `stg_quote`.
3. **Compilação e Validação via Dataform CLI**:
   ```powershell
   npx @dataform/cli compile
   ```
4. **Execução no BigQuery**:
   ```powershell
   npx @dataform/cli run
   ```
5. **Commit e Push no Repositório Git**.

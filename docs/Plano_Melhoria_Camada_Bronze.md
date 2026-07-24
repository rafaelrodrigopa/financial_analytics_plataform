# Plano de Oportunidades de Melhoria: Camada Bronze

Documentação de arquitetura e plano de evolução da **Camada Bronze** na **Financial Analytics Platform**, visando maximizar performance, resiliência, governança e observabilidade de dados no **Google BigQuery**.

---

## 1. Visão Geral das Oportunidades

Embora a **Camada Bronze** atual já atenda aos requisitos fundamentais da Arquitetura Medallion (append-only, metadados de auditoria e particionamento diário por `_ingested_at`), foram identificadas **4 grandes oportunidades de melhoria estratégica** para elevar o pipeline ao padrão Enterprise de Analytics Engineering:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    Oportunidades de Melhoria na Camada Bronze                    │
├──────────────────┬──────────────────────┬──────────────────────┬─────────────────┤
│  1. Performance  │   2. Observabilidade │    3. Integridade    │ 4. Resiliência  │
│ SQL-to-SQL Direct│ Execution Audit Logs │ Hash Payload (_hash) │ Raw JSON Column │
└──────────────────┴──────────────────────┴──────────────────────┴─────────────────┘
```

---

## 2. Detalhamento dos Pilares de Melhoria

### 🚀 Pilar 1: Processamento SQL-to-SQL (BigQuery Direct Promotion)

* **Diagnóstico**: O método `process_landing_to_bronze` realiza o download dos dados da Landing via API do BigQuery para a memória da máquina executora (`to_dataframe()`) e os reenvia via upload.
* **Proposta**: Migrar a promoção da Landing Zone para a Bronze para execução **SQL-to-SQL direta dentro do BigQuery** via `INSERT INTO ... SELECT ...`.
* **Benefícios**:
  - **Desempenho**: Redução do tempo de execução de segundos/minutos para milissegundos.
  - **Escalabilidade**: Isenção de limites de memória RAM Python (Out of Memory - OOM).
  - **Economia de Rede**: Elimina tráfego de dados de entrada/saída entre a máquina local/Cloud Run e o BigQuery.

---

### 📊 Pilar 2: Tabela de Observabilidade e Auditoria (`_pipeline_execution_logs`)

* **Diagnóstico**: O rastreamento atual grava metadados linha a linha (`_execution_id`, `_ingested_at`, `_source`), mas não centraliza métricas sintéticas da execução do pipeline.
* **Proposta**: Criar a tabela de controle `bronze._pipeline_execution_logs` no BigQuery.
* **Esquema Proposto**:
  | Campo | Tipo | Descrição |
  | :--- | :--- | :--- |
  | `execution_id` | `STRING` | UUID único da execução |
  | `table_name` | `STRING` | Nome da tabela processada (ex: `fmp_balance_sheet`) |
  | `rows_read` | `INT64` | Registros lidos da Landing Zone |
  | `rows_written` | `INT64` | Registros gravados na Bronze |
  | `started_at` | `TIMESTAMP` | Timestamp do início da carga |
  | `ended_at` | `TIMESTAMP` | Timestamp de conclusão |
  | `duration_seconds` | `FLOAT64` | Tempo de execução em segundos |
  | `status` | `STRING` | `SUCCESS`, `WARNING` ou `FAILED` |
  | `error_message` | `STRING` | Detalhes em caso de erro |

* **Benefícios**:
  - Rastreabilidade completa para alertas (Slack/Email) e dashboards de saúde de dados (Looker Studio).

---

### 🔒 Pilar 3: Deduplicação e Linhagem via Hash de Payload (`_row_hash`)

* **Diagnóstico**: Ingestões repetidas no mesmo dia acumulam linhas duplicadas sem distinção entre "dados idênticos reingeridos" e "dados atualizados".
* **Proposta**: Calcular uma hash criptográfica (ex: `MD5` ou `SHA256`) das colunas brutas do payload e gravá-la no campo `_row_hash`.
* **Benefícios**:
  - Identificação imediata de duplicatas exatas na Bronze.
  - Otimização do consumo de recursos na camada Silver (Dataform) durante junções e deduplicações.

---

### 📦 Pilar 4: Preservação Semiestruturada Nativa (`_raw_payload` JSON)

* **Diagnóstico**: Alterações súbitas de contrato pela API externa (FMP) podem descartar novos campos não mapeados no schema rígido.
* **Proposta**: Adicionar uma coluna `_raw_payload` utilizando o tipo nativo `JSON` do BigQuery com a resposta inteira sem modificações.
* **Benefícios**:
  - **Garantia de Zero Perda de Dados**: Permite extração SQL retroativa de novos campos sem necessidade de re-ingerir a API.

---

## 3. Matriz de Priorização (Esforço vs. Impacto)

| Item de Melhoria | Impacto no Projeto | Esforço de Implementação | Prioridade Recomendada |
| :--- | :---: | :---: | :---: |
| **1. Processamento SQL-to-SQL** | 🔴 Alto | 🟢 Baixo | 1º (Imediata) |
| **2. Tabela de Logs de Execução** | 🔴 Alto | 🟡 Médio | 2º (Recomendada) |
| **3. Hash de Payload (`_row_hash`)** | 🟡 Médio | 🟡 Médio | 3º (Fase 2) |
| **4. Coluna Nativa `JSON`** | 🟡 Médio | 🟢 Baixo | 4º (Fase 2) |

---

## 4. Plano de Ação para Implementação do Pilar 1 (SQL-to-SQL)

1. Adicionar o método `promote_landing_to_bronze_sql()` em `BronzeService`.
2. Executar query nativa com `INSERT INTO bronze.fmp_table SELECT ..., CURRENT_TIMESTAMP(), 'landing_zone', execution_id FROM landing.table`.
3. Atualizar a suíte de testes em `tests/test_bronze_layer.py`.

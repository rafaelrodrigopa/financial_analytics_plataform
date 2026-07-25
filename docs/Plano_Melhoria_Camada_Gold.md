# Plano de Melhorias e Boas Práticas: Camada Gold (Dataform & Analytics Engineering)

Documentação técnica do plano de otimização, modelagem dimensional avançada, governança e integridade da **Camada Gold** na **Financial Analytics Platform**, utilizando os recursos nativos do **Dataform** no **Google BigQuery**.

---

## 1. Visão Geral do Plano de Melhorias

Com a conclusão da implantação das tabelas de dimensão (`dim_company`, `dim_date`), tabelas fatos (`fact_financial_statements`, `fact_daily_quotes`, `fact_financial_ratios`) e a validação das 28 assertions de integridade, este plano estabelece as diretrizes para elevar a camada analítica a um padrão de **Engenharia de Analytics Sênior**, focando em:

1. **Data Marts Desnormalizados (Wide Tables)**: Criação da camada `marts/` para consumo de BI sem necessidade de JOINs complexos nas ferramentas de ponta (Power BI / Looker Studio).
2. **Inteligência Temporal (Growth Ratios - YoY e QoQ)**: Cálculo de variações percentuais de crescimento em janelas temporais móveis.
3. **Governança Financeira & Flags de Negócio**: Inclusão de indicadores booleanos para identificação imediata de cenários críticos (ex: patrimônio negativo, empresas em prejuízo, alto endividamento).
4. **Integridade Referencial Cruzada (Assertions de Chaves Estrangeiras)**: Garantia de que todas as chaves das tabelas fato possuam correspondência exata nas tabelas de dimensão.
5. **Otimização de Custos e Performance (Materialização Incremental)**: Diretrizes para transição de modelos full-rebuild para carga incremental quando em ambiente de produção com Billing ativado.

---

## 2. Pilares de Otimização e Detalhamento Técnico

### 📌 Melhoria 1: Data Mart de Valuation (`definitions/gold/marts/dm_financial_valuation.sqlx`)
* **Descrição**: Criar um Data Mart unificado que cruza em tempo real a cotação mais recente (`fact_daily_quotes`), os últimos demonstrativos financeiros (`fact_financial_statements`), os indicadores de rentabilidade (`fact_financial_ratios`) e o cadastro da empresa (`dim_company`).
* **Múltiplos e Indicadores Calculados**:
  * **P/L (Price to Earnings)**: `SAFE_DIVIDE(preco_atual, lucro_por_acao)`
  * **P/VP (Price to Book Value)**: `SAFE_DIVIDE(valor_mercado, patrimonio_liquido)`
  * **P/S (Price to Sales)**: `SAFE_DIVIDE(valor_mercado, receita_liquida)`
  * **FCF Yield (%)**: `SAFE_DIVIDE(fluxo_caixa_livre, valor_mercado) * 100`
  * **EV / EBIT**: `SAFE_DIVIDE(valor_mercado + divida_liquida, lucro_operacional)`
* **Benefício**: Disponibilização de uma visão consolidada de Valuation pronta para relatórios e dashboards executivos, sem necessidade de relacionamentos complexos no Power BI.

---

### 📌 Melhoria 2: Indicadores de Crescimento Temporal (YoY e QoQ)
* **Descrição**: Incorporar métricas de crescimento em relação ao trimestre anterior (*Quarter-over-Quarter*) e ao mesmo trimestre do ano anterior (*Year-over-Year*) utilizando funções de janela SQL (`LAG`).
* **Lógica SQL**:
  ```sql
  -- Crescimento de Receita YoY (%)
  SAFE_DIVIDE(
    receita_liquida - LAG(receita_liquida, 4) OVER (PARTITION BY codigo_ativo ORDER BY data_referencia),
    ABS(LAG(receita_liquida, 4) OVER (PARTITION BY codigo_ativo ORDER BY data_referencia))
  ) * 100 AS crescimento_receita_yoy,

  -- Crescimento do Lucro Líquido QoQ (%)
  SAFE_DIVIDE(
    lucro_liquido - LAG(lucro_liquido, 1) OVER (PARTITION BY codigo_ativo ORDER BY data_referencia),
    ABS(LAG(lucro_liquido, 1) OVER (PARTITION BY codigo_ativo ORDER BY data_referencia))
  ) * 100 AS crescimento_lucro_qoq
  ```
* **Benefício**: Suporte nativo a análise de tendência temporal e identificação de aceleração de resultados corporativos.

---

### 📌 Melhoria 3: Flags de Governança e Alertas Financeiros
* **Descrição**: Adicionar colunas booleanas (`TRUE`/`FALSE`) nas tabelas fato para categorização rápida e filtros intuitivos em ferramentas de Self-Service BI.
* **Flags Mapeadas**:
  * `eh_empresa_prejuizo`: `IF(lucro_liquido < 0, TRUE, FALSE)`
  * `eh_patrimonio_negativo`: `IF(patrimonio_liquido < 0, TRUE, FALSE)` (alerta de distorção de ROE)
  * `eh_caixa_liquido_positivo`: `IF(divida_liquida < 0, TRUE, FALSE)` (indica caixa superior à dívida)

---

### 📌 Melhoria 4: Assertions de Integridade Referencial (FK Validation)
* **Descrição**: Criar testes customizados em `definitions/gold/assertions/` para garantir a integridade referencial entre fatos e dimensões.
* **Assertions a Criar**:
  * **`assert_fk_facts_to_dim_company.sqlx`**: Garante que todo `codigo_ativo` presente nas tabelas fato (`fact_financial_statements`, `fact_daily_quotes`, `fact_financial_ratios`) exista previamente em `dim_company`.
  * **`assert_fk_facts_to_dim_date.sqlx`**: Garante que toda `data_referencia` exista no calendário `dim_date`.

---

### 📌 Melhoria 5: Estratégia de Atualização Incremental para a Camada Gold
* **Descrição**: Mapear a transição dos modelos fato de `type: "table"` para `type: "incremental"` no Dataform para cenários de produção.
* **Observação Arquitetural sobre o BigQuery Sandbox (Free Tier)**:
  No ambiente Sandbox do BigQuery (sem conta de faturamento ativada), instruções DML (`MERGE`/`INSERT INTO`) resultam em bloqueio do projeto. Portanto, mantemos `type: "table"` no ambiente de testes/Sandbox e deixamos a sintaxe `${when(incremental(), ...)}` mapeada para ativação em produção.

---

## 3. Matriz de Priorização das Melhorias

| Ordem | Melhoria | Esforço | Impacto | Categoria |
| :---: | :--- | :---: | :---: | :--- |
| **1** | Data Mart de Valuation (`dm_financial_valuation.sqlx`) | Médio | **Alto** | Analytics Engineering |
| **2** | Assertions de Integridade Referencial (FK Check) | Baixo | **Alto** | Data Quality |
| **3** | Indicadores de Crescimento Temporal (YoY e QoQ) | Médio | **Alto** | Business Intelligence |
| **4** | Flags de Governança e Alertas Financeiros | Baixo | Médio | Analytics Engineering |
| **5** | Materialização Incremental (Produção) | Médio | Médio | Performance & Ops |

---

## 4. Próximos Passos de Execução

1. Validação do plano de melhorias com o usuário.
2. Implementação das melhorias prioritárias em lote.
3. Validação via Dataform CLI (`npx @dataform/cli compile` e `npx @dataform/cli run`).
4. Atualização da documentação geral do projeto.

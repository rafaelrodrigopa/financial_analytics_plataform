# Plano de Implementação: Camada Gold (Data Marts & Financial Analytics)

Documentação técnica completa do plano de implementação da **Camada Gold** na **Financial Analytics Platform**, utilizando a ferramenta nativa **Dataform** no **Google BigQuery** para modelagem dimensional (Star Schema), cálculo de indicadores financeiros de valuation/performance e disponibilização de dados em **Português** para consumo em dashboards (PowerBI, Looker Studio).

---

## 1. Visão Geral da Arquitetura Gold

A Camada Gold é a camada de **Analytics, BI e Consumo Final (Data Marts)**. Ela consome as tabelas higienizadas da **Camada Silver** e as transforma em dimensões padronizadas e fatos consolidados com linguagem orientada ao negócio.

```text
┌──────────────┐     ┌──────────────┐     ┌────────────────────────────────────────────────────────┐
│ Bronze Layer │ ──> │ Silver Layer │ ──> │                       Gold Layer                       │
│ (Raw Data)   │     │ (Clean Data) │     │                  (Analytics Star Schema)               │
└──────────────┘     └──────────────┘     └────────────────────────────────────────────────────────┘
                                            ├── Dimensões: dim_company, dim_date
                                            └── Fatos: fact_financial_statements,
                                                       fact_daily_quotes,
                                                       fact_financial_ratios
```

---

## 2. Pilares da Camada Gold

1. **Modelagem Dimensional (Star Schema)**:
   * **Dimensões**: Cadastros reutilizáveis de empresas e calendário temporal.
   * **Fatos**: Dados transacionais e periódicos consolidados (Demonstrativos, Cotações e Ratios).
2. **Nomenclatura Orientada a Negócio em Português**:
   * Tradução e padronização de todos os nomes de atributos (`total_assets` ➔ `ativo_total`, `revenue` ➔ `receita_liquida`, `net_income` ➔ `lucro_liquido`).
3. **Cálculo de Indicadores Financeiros (Financial Ratios & KPIs)**:
   * **Margens**: Margem Bruta (`gross_margin`), Margem Operacional (`operating_margin`), Margem Líquida (`net_margin`).
   * **Retornos & Estrutura**: ROE (Retorno sobre Patrimônio), Liquidez Corrente, Dívida Líquida / Patrimônio.
4. **Governança & Assertions Nativas**:
   * Testes de integridade referencial entre Tabelas Fato e Dimensões (`uniqueKey`, `nonNull`, `foreignKey`).

---

## 3. Mapeamento de Data Marts e Modelos na Camada Gold

Os **Data Marts** constituem a entrega final da Camada Gold. Cada Data Mart é modelado para atender a um domínio de negócio específico e alimentar diretamente relatórios e dashboards no Power BI e Looker Studio.

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    GOLD LAYER (DATA MARTS)                                      │
├────────────────────────────────┬────────────────────────────────┬───────────────────────────────┤
│ Data Mart 1: Desempenho &      │ Data Mart 2: Mercado &         │ Data Mart 3: Visão Executiva  │
│ Valuation                      │ Cotações                       │ 360° da Empresa               │
│ (Análise Fundamentalista,      │ (Acompanhamento de Preços,     │ (Cadastro Corporativo, Setor, │
│ Margens, ROE, Dívida Líquida)  │ Volume e Valor de Mercado)     │ Indicadores Chave de Mercado) │
└────────────────────────────────┴────────────────────────────────┴───────────────────────────────┘
```

### 📐 Dimensões (`definitions/gold/dimensions/`)

| Tabela / Dimensão | Modelo SQLX | Tabela Origem (Silver) | Descrição |
| :--- | :--- | :--- | :--- |
| `gold.dim_company` | `dim_company.sqlx` | `silver.dim_company_profile` | Cadastro corporativo higienizado com aliases em português. |
| `gold.dim_date` | `dim_date.sqlx` | Gerador SQL / Calendário | Dimensão temporal nativa (Ano, Trimestre, Mês, Nome do Mês, Dia). |

### 📊 Fatos & Data Marts (`definitions/gold/facts/` e `definitions/gold/marts/`)

| Tabela / Data Mart | Modelo SQLX | Origens (Silver/Gold) | Domínio do Data Mart |
| :--- | :--- | :--- | :--- |
| `gold.fact_financial_statements` | `fact_financial_statements.sqlx` | `stg_balance_sheet`, `stg_income_statement`, `stg_cash_flow` | **Data Mart Financeiro**: DRE, Balanço e Fluxo de Caixa unificados em português. |
| `gold.fact_daily_quotes` | `fact_daily_quotes.sqlx` | `silver.stg_quote` | **Data Mart de Mercado**: Cotações diárias, oscilações e volumes negociados. |
| `gold.fact_financial_ratios` | `fact_financial_ratios.sqlx` | `gold.fact_financial_statements` | **Data Mart de Valuation**: Indicadores de Margens (Bruta/Operacional/Líquida), ROE e FCF. |
| `gold.dm_financial_valuation` | `dm_financial_valuation.sqlx` | `gold.fact_financial_statements`, `gold.fact_financial_ratios`, `gold.dim_company` | **Data Mart Consolidado de Valuation**: Visão pronta para análise de ações e relatórios de investimento. |

---

## 4. Etapas Detalhadas de Implementação

### 📌 Etapa 1: Estruturação dos Arquivos e Diretórios no Dataform
- Criar a estrutura de diretórios em `definitions/gold/`:
  - `definitions/gold/dimensions/`
  - `definitions/gold/facts/`
  - `definitions/gold/assertions/`

### 📌 Etapa 2: Desenvolvimento das Dimensões (`dim_company` e `dim_date`)
- **`dim_company.sqlx`**:
  * Tradução dos atributos para português (`codigo_ativo`, `nome_empresa`, `moeda`, `bolsa`, `industria`, `setor`, `pais`, `valor_mercado`).
  * Inclusão do dicionário `columns` em português e tags `["gold", "dimensions"]`.
- **`dim_date.sqlx`**:
  * Criação de gerador automático de calendário temporal abrangendo os anos dos demonstrativos (ex: 2010 a 2030).

### 📌 Etapa 3: Desenvolvimento do Fato Consolidado (`fact_financial_statements`)
- **`fact_financial_statements.sqlx`**:
  * Realizar `FULL OUTER JOIN` / `LEFT JOIN` entre `stg_income_statement`, `stg_balance_sheet` e `stg_cash_flow` usando as chaves `(symbol, date, period)`.
  * Tradução de todos os campos financeiros para português (`receita_liquida`, `lucro_bruto`, `lucro_operacional`, `lucro_liquido`, `ativo_total`, `passivo_total`, `patrimonio_liquido`, `divida_liquida`, `fluxo_caixa_operacional`, `capex`, `fluxo_caixa_livre`).
  * Inclusão de `columns` e `assertions` (`uniqueKey: ["codigo_ativo", "data_referencia", "periodo"]`).

### 📌 Etapa 4: Desenvolvimento do Fato de Cotações (`fact_daily_quotes`)
- **`fact_daily_quotes.sqlx`**:
  * Seleção e tradução da tabela `stg_quote` (`codigo_ativo`, `preco_atual`, `variacao_percentual`, `variacao_nominal`, `preco_minimo_dia`, `preco_maximo_dia`, `preco_maximo_52sem`, `preco_minimo_52sem`, `valor_mercado`, `volume_negociado`).
  * Configuração de particionamento por `data_ingestao` e clusterização por `codigo_ativo`.

### 📌 Etapa 5: Desenvolvimento do Fato de Indicadores Financeiros (`fact_financial_ratios`)
- **`fact_financial_ratios.sqlx`**:
  * Cálculo em SQL dos principais índices financeiros:
    * **Margem Bruta**: `SAFE_DIVIDE(lucro_bruto, receita_liquida) * 100`
    * **Margem Operacional**: `SAFE_DIVIDE(lucro_operacional, receita_liquida) * 100`
    * **Margem Líquida**: `SAFE_DIVIDE(lucro_liquido, receita_liquida) * 100`
    * **ROE (Retorno s/ Patrimônio)**: `SAFE_DIVIDE(lucro_liquido, patrimonio_liquido) * 100`
    * **Conversão de Caixa (FCF/Lucro)**: `SAFE_DIVIDE(fluxo_caixa_livre, lucro_liquido) * 100`

### 📌 Etapa 6: Assertions de Qualidade e Integridade da Camada Gold
- Adicionar testes de unicidade, não-nulos e validações matemáticas para os indicadores (ex: margens entre -1000% e +1000%).

### 📌 Etapa 7: Compilação, Execução no BigQuery e Documentação
- Compilar com `npx @dataform/cli compile`.
- Executar e materializar no BigQuery (`npx @dataform/cli run`).
- Validação das tabelas no dataset `gold` do BigQuery.

---

## 5. Plano de Verificação e Validação

```powershell
# Compilar projeto Dataform incluindo a Camada Gold
npx @dataform/cli compile

# Executar apenas os modelos e testes da Camada Gold no BigQuery
npx @dataform/cli run --tags gold
```

### Consulta SQL de Teste no BigQuery (`gold`)
```sql
SELECT 
  c.nome_empresa,
  c.setor,
  f.data_referencia,
  f.periodo,
  f.receita_liquida,
  f.lucro_liquido,
  r.margem_liquida_pct,
  r.roe_pct
FROM `civil-glyph-503402-c9.gold.fact_financial_statements` f
JOIN `civil-glyph-503402-c9.gold.dim_company` c 
  ON f.codigo_ativo = c.codigo_ativo
LEFT JOIN `civil-glyph-503402-c9.gold.fact_financial_ratios` r
  ON f.codigo_ativo = r.codigo_ativo 
 AND f.data_referencia = r.data_referencia 
 AND f.periodo = r.periodo
LIMIT 10;
```

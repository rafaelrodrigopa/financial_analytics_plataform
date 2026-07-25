# Camada Gold: Data Marts & Analytics (Dataform)

Este diretório contém a modelagem dimensional e os Data Marts da **Camada Gold** da Financial Analytics Platform.

## Estrutura de Diretórios:

- `dimensions/`: Tabelas de dimensão em português (`dim_company.sqlx`, `dim_date.sqlx`).
- `facts/`: Tabelas fatos transacionais e consolidadas (`fact_financial_statements.sqlx`, `fact_daily_quotes.sqlx`, `fact_financial_ratios.sqlx`).
- `marts/`: Data Marts consolidados prontos para consumo por BI (`dm_financial_valuation.sqlx`).
- `assertions/`: Testes de integridade referencial e validações de indicadores.

// Declarações de origem das tabelas da Camada Bronze no BigQuery para referência nos modelos do Dataform via ${ref("fmp_...")}
// O campo 'database' é resolvido dinamicamente pelo Dataform a partir do projeto GCP configurado no ambiente.

declare({
  schema: "bronze",
  name: "fmp_balance_sheet",
  description: "Tabela bruta histórica de Balanço Patrimonial (Balance Sheet Statement) da API FMP.",
});

declare({
  schema: "bronze",
  name: "fmp_income_statement",
  description: "Tabela bruta histórica de Demonstrativo de Resultado (Income Statement) da API FMP.",
});

declare({
  schema: "bronze",
  name: "fmp_cash_flow",
  description: "Tabela bruta histórica de Fluxo de Caixa (Cash Flow Statement) da API FMP.",
});

declare({
  schema: "bronze",
  name: "fmp_company_profile",
  description: "Tabela bruta histórica de Perfil Corporativo da API FMP.",
});

declare({
  schema: "bronze",
  name: "fmp_quote",
  description: "Tabela bruta histórica de Cotações em Tempo Real da API FMP.",
});

# Documentação de Limitações da API - Financial Modeling Prep (FMP)

Este documento descreve o funcionamento, os limites de taxa (Rate Limits) e as estratégias de ingestão adotadas no projeto para lidar com a API externa **Financial Modeling Prep (FMP)**.

---

## 1. Visão Geral da API

A plataforma utiliza a API **Financial Modeling Prep (FMP)** para extração de demonstrações financeiras e dados de cotação de mercado.

### Endpoints Utilizados:
- **`quote`**: Cotação em tempo real e métricas de mercado.
- **`profile`**: Perfil cadastral da empresa (setores, indústrias, valor de mercado, etc.).
- **`income-statement`**: Demonstrativo do Resultado do Exercício (DRE).
- **`balance-sheet-statement`**: Balanço Patrimonial.
- **`cash-flow-statement`**: Demonstração do Fluxo de Caixa.

---

## 2. Limitações do Plano Gratuito (Free Tier)

A chave de API no plano gratuito/básico impõe restrições de volume e taxa de chamadas:

| Parâmetro | Limite no Plano Gratuito |
| :--- | :--- |
| **Requisições Diárias** | ~250 requisições / dia |
| **Requisições por Minuto** | ~30 requisições / minuto |
| **Código HTTP de Limite** | `429 Too Many Requests` |

### Multiplicador de Chamadas por Empresa:
Como o pipeline extrai **5 endpoints diferentes** por empresa, a fórmula de consumo de requisições é:

$$\text{Total de Requisições} = \text{Número de Empresas} \times 5$$

- Para **24 empresas**: $24 \times 5 = 120 \text{ chamadas de API}$.
- Ao atingir o limite diário da cota gratuita, a API passa a responder com erro `HTTP 429`.

---

## 3. Tratamento de Erros e Resiliência no Código

Para evitar falhas abruptas e garantir a estabilidade do pipeline:

1. **Retry Automático com Exponential Backoff** (`src/connectors/financial_modeling_prep.py`):
   - Quando a API retorna `HTTP 429`, o conector aguarda automaticamente alguns segundos antes de tentar novamente, dobrando o tempo de espera a cada tentativa.
2. **Pausa Estratégica entre Empresas** (`src/services/ingestion_service.py`):
   - Adicionada uma pausa de `0.15s` a cada empresa processada para respeitar o limite de chamadas por segundo.

---

## 4. Estratégia de Ingestão Incremental (Crescimento Diário)

Como a cota da API é renovada a cada 24 horas, adotamos uma estratégia de ingestão diária:

- **Dia 1**: Ingestão do 1º lote de 24 empresas $\rightarrow$ **120 demonstrações financeiras gravadas**.
- **Dia 2**: Ingestão do 2º lote de +24 empresas $\rightarrow$ **Chegando a 48 empresas (240 demonstrações)**.
- **Dia 3**: Ingestão do 3º lote de +24 empresas $\rightarrow$ **Chegando a 72 empresas (360 demonstrações)**.

### Configuração no BigQuery:
Para acumular novas empresas sem apagar as existentes:
- **`WRITE_TRUNCATE`**: Substitui a tabela inteira (usado na carga inicial).
- **`WRITE_APPEND`**: Anexa os novos registros mantendo os anteriores (usado na carga diária).

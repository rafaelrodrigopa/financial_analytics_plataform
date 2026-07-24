# Financial Analytics Platform 🚀

 Uma plataforma robusta de Engenharia de Dados desenvolvida para ingestão, processamento e modelagem de dados financeiros de empresas de capital aberto (Financial Modeling Prep API), utilizando a **Arquitetura Medallion** no **Google BigQuery**.

---

## 🏗️ Arquitetura do Pipeline

O pipeline segue as melhores práticas de Analytics Engineering com organização em camadas (Medallion Architecture):

```
┌─────────────────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  API FMP / Financial    │ ──> │ Landing Zone │ ──> │ Bronze Layer │ ──> │ Silver Layer │ ──> │ Gold Layer  │
│  Modeling Prep          │     │ (Raw Staged) │     │ (Raw Historic│     │ (Clean Data) │     │ (Analytics) │
└─────────────────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
```

### 🧱 Camadas de Dados (BigQuery Datasets)
- **`landing`**: Zona de staging temporária para armazenamento dos payloads brutos consumidos das APIs.
- **`bronze`**: Armazenamento bruto persistente e histórico com marcação de data de ingestão.
- **`silver`**: Dados limpos, desduplicados, tipados e padronizados para análise.
- **`gold`**: Camada analítica otimizada com data marts para dashboards e relatórios financeiros.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.12+
- **Data Warehouse**: Google BigQuery
- **Bibliotecas**: `google-cloud-bigquery`, `pandas-gbq`, `pyarrow`, `python-dotenv`
- **Ambiente Virtual**: `venv`

---

## 📂 Estrutura do Repositório

```text
financial-analytics-platform/
│
├── .env.example                      # Modelo de variáveis de ambiente (sem segredos)
├── .gitignore                        # Regras de exclusão de credenciais e venv
├── README.md                         # Documentação pública do repositório
├── requirements.txt                  # Dependências do projeto
│
├── src/
│   ├── core/
│   │   └── config.py                 # Gerenciador de configurações de ambiente
│   └── warehouse/
│       └── bigquery_client.py        # Cliente de abstração do BigQuery
│
└── tests/
    └── test_bigquery_connection.py  # Script de teste de conexão com o BigQuery
```

---

## 🚀 Como Configurar e Executar

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/financial-analytics-platform.git
cd financial-analytics-platform
```

### 2. Criar e Ativar o Ambiente Virtual
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / MacOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com base no `.env.example`:

```env
# Financial Modeling Prep API
FMP_API_KEY=seu_api_key_aqui
FMP_BASE_URL=https://financialmodelingprep.com/stable

# Google BigQuery
GOOGLE_APPLICATION_CREDENTIALS=credenciais/chave_conta_servico.json
GCP_PROJECT_ID=seu_gcp_project_id

# Datasets
BQ_DATASET_LANDING=landing
BQ_DATASET_BRONZE=bronze
BQ_DATASET_SILVER=silver
BQ_DATASET_GOLD=gold
```

> ⚠️ **Importante**: Nunca envie o arquivo `.env` ou chaves de serviço `.json` para o controle de versão. Adicione-os sempre ao `.gitignore`.

### 5. Autenticação GCP
Coloque o arquivo JSON da sua Service Account no diretório `credenciais/chave_conta_servico.json` e assegure-se que a conta de serviço possui o papel de **BigQuery Admin** ou **BigQuery User / Data Editor** no seu projeto no Google Cloud Console.

### 6. Testar Conexão
Para verificar a conexão com o BigQuery e listar os datasets configurados:
```bash
python tests/test_bigquery_connection.py
```

---

## 📝 Licença

Este projeto está sob a licença MIT. Sinta-se à vontade para utilizar e contribuir.

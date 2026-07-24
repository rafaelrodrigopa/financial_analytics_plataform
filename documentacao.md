# Documentação da Configuração Inicial do Pipeline de Dados

## 1. Visão Geral do Pipeline

Esta aplicação estrutura um pipeline de análise financeira (**Financial Analytics Platform**) seguindo a **Arquitetura Medallion** no **Google BigQuery**.

```
┌─────────────────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  API FMP / Financial    │ ──> │ Landing Zone │ ──> │ Bronze Layer │ ──> │ Silver Layer │ ──> │ Gold Layer  │
│  Modeling Prep          │     │   (Raw API)  │     │ (Raw Historic│     │ (Clean Data) │     │ (Analytics) │
└─────────────────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
```

### Datasets Configurados no BigQuery:
- **`landing`**: Camada de ingestão bruta (staged raw data).
- **`bronze`**: Dados brutos históricos armazenados com schema consistente.
- **`silver`**: Dados limpos, padronizados e enriquecidos.
- **`gold`**: Camada analítica otimizada para BI e modelagem financeira.

---

## 2. Configuração do Ambiente Virtual (`.venv`)

Para garantir o isolamento e reprodutibilidade do projeto, foi configurado um ambiente virtual Python:

1. **Criação do Ambiente Virtual**:
   ```bash
   python -m venv .venv
   ```

2. **Bibliotecas Instaladas**:
   - **`google-cloud-bigquery`**: SDK oficial para integração com o Google BigQuery.
   - **`pandas-gbq`**: Integração entre DataFrames `pandas` e BigQuery via `pyarrow`.
   - **`pyarrow`**: Engine de alta performance para conversão de tipos de dados.
   - **`python-dotenv`**: Carregamento automático das variáveis de ambiente (`.env`).

3. **Arquivos de Suporte do Projeto**:
   - `requirements.txt`: Mapeamento completo das versões instaladas.
   - `.gitignore`: Proteção de credenciais (`.json`), arquivos locais (`.env`) e pastas do ambiente virtual (`.venv/`).

---

## 3. Estrutura de Arquivos e Variáveis de Ambiente

### Estrutura do Projeto:
```text
financial-analytics-platform/
│
├── .env                              # Variáveis de ambiente e segredos
├── .gitignore                        # Regras de exclusão do Git
├── README.md                         # Documentação pública do repositório
├── documentacao.md                   # Documentação detalhada interna
├── requirements.txt                  # Lista de dependências Python
│
├── credenciais/
│   └── chave_conta_servico.json      # Chave JSON de Service Account GCP
│
├── src/
│   ├── core/
│   │   └── config.py                 # Módulo central de configurações (Pydantic/Dotenv)
│   └── warehouse/
│       └── bigquery_client.py        # Cliente de abstração do BigQuery
│
└── tests/
    └── test_bigquery_connection.py  # Script de teste de conexão com o BigQuery
```

### Ajustes no `.env`:
```env
# Google BigQuery
GOOGLE_APPLICATION_CREDENTIALS=credenciais/chave_conta_servico.json
GCP_PROJECT_ID=civil-glyph-503402-c9

BQ_DATASET_LANDING=landing
BQ_DATASET_BRONZE=bronze
BQ_DATASET_SILVER=silver
BQ_DATASET_GOLD=gold
```

### Módulo `src/core/config.py`:
Carrega automaticamente as variáveis do `.env` e provê a instância `settings`:
```python
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_PROJECT_ID = PROJECT_ID
    LANDING = os.getenv("BQ_DATASET_LANDING")
    BRONZE = os.getenv("BQ_DATASET_BRONZE")
    SILVER = os.getenv("BQ_DATASET_SILVER")
    GOLD = os.getenv("BQ_DATASET_GOLD")
    FMP_API_KEY = os.getenv("FMP_API_KEY")

settings = Settings()
```

---

## 4. Autenticação e Permissões no Google Cloud Platform (GCP)

- **Conta de Serviço (Service Account)**:
  `financial-platform@civil-glyph-503402-c9.iam.gserviceaccount.com`
- **ID do Projeto no GCP**: `civil-glyph-503402-c9`
- **Papel IAM Atribuído**: **Proprietário / BigQuery Admin** no nível do Projeto.

---

## 5. Abstração do Cliente BigQuery (`BigQueryClient`)

Em `src/warehouse/bigquery_client.py`, foi criada a classe `BigQueryClient` que abstrai a comunicação com o serviço:

```python
from google.cloud import bigquery
from src.core.config import settings

class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client(
            project=settings.PROJECT_ID
        )

    def list_datasets(self):
        """
        Lista todos os datasets ativos no projeto GCP.
        """
        return list(self.client.list_datasets(project=self.client.project, include_all=True))
```

---

## 6. Validação e Execução

O script de teste `tests/test_bigquery_connection.py` valida a conexão e retorna a listagem dos datasets:

```python
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.warehouse.bigquery_client import BigQueryClient

def test_bigquery_connection():
    bq = BigQueryClient()
    datasets = bq.list_datasets()

    if not datasets:
        print("Conexão estabelecida com sucesso! Nenhum dataset encontrado no projeto no momento.")
    else:
        print("Datasets encontrados no projeto:")
        for dataset in datasets:
            print(f"- {dataset.dataset_id}")

if __name__ == "__main__":
    test_bigquery_connection()
```

### Comando para ativação e teste no PowerShell:
```powershell
.\.venv\Scripts\activate
python tests/test_bigquery_connection.py
```

### Saída de Sucesso:
```text
Datasets encontrados no projeto:
- bronze
- gold
- landing
- silver
```

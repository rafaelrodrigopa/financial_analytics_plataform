import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.warehouse.bigquery_client import BigQueryClient


def test_bigquery_connection():
    """
    Testa a conexão com o BigQuery e lista todos os datasets disponíveis.
    """
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

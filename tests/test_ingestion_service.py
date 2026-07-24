import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.ingestion_service import IngestionService


def test_top_100_ingestion():
    """
    Executa a ingestão das 100 maiores empresas para popular o dataset Landing do BigQuery.
    """
    ingestion = IngestionService()  # Usa a lista padrão de 100 empresas
    ingestion.run_landing_ingestion(limit_statements=5)


if __name__ == "__main__":
    test_top_100_ingestion()

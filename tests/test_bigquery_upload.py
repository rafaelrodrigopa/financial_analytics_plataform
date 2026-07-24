import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.connectors import FinancialModelingPrep
from src.core.config import settings
from src.warehouse.bigquery_client import BigQueryClient


def test_bigquery_upload_landing():
    """
    Testa o fluxo completo de ingestão e carga na camada Landing do BigQuery:
    Extract (FMP API) -> Load (BigQuery Landing)
    """
    print(f"Projeto GCP: {settings.PROJECT_ID}")
    print(f"Dataset Landing: {settings.LANDING}")

    fmp = FinancialModelingPrep()
    bq = BigQueryClient()

    # 1. Extrair e Upload Quote
    print("\n--- Processando Quote ---")
    df_quote = fmp.get_quote(settings.DEFAULT_SYMBOL)
    bq.upload_dataframe(
        dataframe=df_quote, dataset_id=settings.LANDING, table_id="quote", write_disposition="WRITE_TRUNCATE"
    )

    # 2. Extrair e Upload Profile
    print("\n--- Processando Profile ---")
    df_profile = fmp.get_company_profile(settings.DEFAULT_SYMBOL)
    bq.upload_dataframe(
        dataframe=df_profile,
        dataset_id=settings.LANDING,
        table_id="company_profile",
        write_disposition="WRITE_TRUNCATE",
    )

    # 3. Extrair e Upload Income Statement
    print("\n--- Processando Income Statement ---")
    df_income = fmp.get_income_statement(settings.DEFAULT_SYMBOL, limit=5)
    bq.upload_dataframe(
        dataframe=df_income,
        dataset_id=settings.LANDING,
        table_id="income_statement",
        write_disposition="WRITE_TRUNCATE",
    )

    # 4. Extrair e Upload Balance Sheet
    print("\n--- Processando Balance Sheet ---")
    df_balance = fmp.get_balance_sheet(settings.DEFAULT_SYMBOL, limit=5)
    bq.upload_dataframe(
        dataframe=df_balance, dataset_id=settings.LANDING, table_id="balance_sheet", write_disposition="WRITE_TRUNCATE"
    )

    # 5. Extrair e Upload Cash Flow
    print("\n--- Processando Cash Flow ---")
    df_cash = fmp.get_cash_flow(settings.DEFAULT_SYMBOL, limit=5)
    bq.upload_dataframe(
        dataframe=df_cash, dataset_id=settings.LANDING, table_id="cash_flow", write_disposition="WRITE_TRUNCATE"
    )

    print("\nFluxo de carga para a camada Landing finalizado com sucesso!")


if __name__ == "__main__":
    test_bigquery_upload_landing()

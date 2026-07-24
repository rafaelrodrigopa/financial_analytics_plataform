import unittest
import uuid
from unittest.mock import MagicMock

import pandas as pd
from google.cloud import bigquery
from src.core.config import settings
from src.services.bronze_service import BronzeService
from src.warehouse.bigquery_client import BigQueryClient


class TestBronzeServiceUnit(unittest.TestCase):
    """
    Testes unitários isolados para o serviço BronzeService utilizando Mocks.
    """

    def setUp(self):
        self.mock_bq_client = MagicMock()
        self.bronze_service = BronzeService(bq_client=self.mock_bq_client)

    def test_load_dataframe_to_bronze_adds_audit_fields(self):
        """
        Verifica se os campos de auditoria (_ingested_at, _source, _execution_id)
        são inseridos no DataFrame antes do envio ao BigQuery.
        """
        sample_df = pd.DataFrame(
            [
                {"symbol": "AAPL", "revenue": 1000000, "netIncome": 250000},
                {"symbol": "MSFT", "revenue": 1200000, "netIncome": 300000},
            ]
        )

        table_id = "test_fmp_income_statement"
        custom_exec_id = f"exec-unit-{uuid.uuid4().hex[:8]}"

        self.bronze_service.load_dataframe_to_bronze(
            dataframe=sample_df,
            table_id=table_id,
            source="unit_test",
            execution_id=custom_exec_id,
        )

        # Verifica se upload_dataframe foi chamado exatamente 1 vez
        self.mock_bq_client.upload_dataframe.assert_called_once()

        # Extrai os argumentos com os quais upload_dataframe foi invocado
        call_kwargs = self.mock_bq_client.upload_dataframe.call_args.kwargs
        uploaded_df = call_kwargs["dataframe"]

        # Validações dos campos de auditoria
        self.assertIn("_ingested_at", uploaded_df.columns)
        self.assertIn("_source", uploaded_df.columns)
        self.assertIn("_execution_id", uploaded_df.columns)

        self.assertEqual(uploaded_df["_source"].iloc[0], "unit_test")
        self.assertEqual(uploaded_df["_execution_id"].iloc[0], custom_exec_id)

        # Validação do modo de escrita (WRITE_APPEND)
        self.assertEqual(call_kwargs["write_disposition"], "WRITE_APPEND")

        # Validação da configuração de particionamento e clusterização
        tp = call_kwargs["time_partitioning"]
        self.assertIsNotNone(tp)
        self.assertEqual(tp.field, "_ingested_at")
        self.assertEqual(tp.type_, bigquery.TimePartitioningType.DAY)

        self.assertEqual(call_kwargs["clustering_fields"], ["symbol"])

    def test_empty_dataframe_omits_upload(self):
        """
        Garante que DataFrames vazios não chamam o upload_dataframe no BigQuery.
        """
        empty_df = pd.DataFrame()
        self.bronze_service.load_dataframe_to_bronze(empty_df, table_id="empty_table")
        self.mock_bq_client.upload_dataframe.assert_not_called()


class TestBronzeLayerIntegration(unittest.TestCase):
    """
    Testes de integração reais com o Google BigQuery (Dataset Bronze).
    Valida a conexão, criação de tabelas, gravação de metadados, integridade do payload
    e configuração de particionamento/clusterização.
    """

    @classmethod
    def setUpClass(cls):
        try:
            cls.bq_client = BigQueryClient()
            cls.bronze_service = BronzeService(bq_client=cls.bq_client)
            # Testa conexão listando datasets
            cls.bq_client.list_datasets()
            cls.connection_available = True
        except Exception as e:
            cls.connection_available = False
            print(f"[SKIP] Conexão com o BigQuery indisponível para testes de integração: {e}")

    def setUp(self):
        if not self.connection_available:
            self.skipTest("Google BigQuery indisponível ou sem credenciais válidas.")

    def test_live_bronze_ingestion_and_metadata_validation(self):
        """
        Executa uma ingestão simulada no BigQuery (dataset bronze) e valida:
        1. Criação/Persistência da tabela no dataset bronze.
        2. Presença e valores corretos dos metadados (_ingested_at, _source, _execution_id).
        3. Integridade do payload financeiro inserido.
        4. Particionamento por _ingested_at e clusterização por symbol.
        """
        table_id = "test_integration_fmp_balance_sheet"
        execution_id = f"test-exec-{uuid.uuid4().hex[:8]}"
        source_name = "fmp_integration_test"

        sample_payload = pd.DataFrame(
            [
                {
                    "symbol": "AAPL",
                    "date": "2026-03-31",
                    "calendarYear": "2026",
                    "period": "Q1",
                    "totalAssets": 350000000000.0,
                    "totalLiabilities": 290000000000.0,
                    "netIncome": 24000000000.0,
                },
                {
                    "symbol": "MSFT",
                    "date": "2026-03-31",
                    "calendarYear": "2026",
                    "period": "Q1",
                    "totalAssets": 410000000000.0,
                    "totalLiabilities": 200000000000.0,
                    "netIncome": 22000000000.0,
                },
            ]
        )

        # 1. Executa a gravação na camada Bronze
        self.bronze_service.load_dataframe_to_bronze(
            dataframe=sample_payload,
            table_id=table_id,
            source=source_name,
            execution_id=execution_id,
        )

        # 2. Valida existência e metadados de infraestrutura da tabela no BigQuery
        table_ref = f"{self.bq_client.project_id}.{settings.BRONZE}.{table_id}"
        table_metadata = self.bq_client.client.get_table(table_ref)

        self.assertIsNotNone(table_metadata)
        self.assertGreater(table_metadata.num_rows, 0)

        # Valida Particionamento por _ingested_at
        self.assertIsNotNone(table_metadata.time_partitioning)
        self.assertEqual(table_metadata.time_partitioning.field, "_ingested_at")

        # Valida Clusterização por symbol
        self.assertIsNotNone(table_metadata.clustering_fields)
        self.assertIn("symbol", table_metadata.clustering_fields)

        # 3. Executa Query SQL para verificar gravação de registros e integridade do payload
        query = f"""
            SELECT symbol, date, calendarYear, period, totalAssets, totalLiabilities, netIncome,
                   _ingested_at, _source, _execution_id
            FROM `{table_ref}`
            WHERE _execution_id = @execution_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("execution_id", "STRING", execution_id),
            ]
        )
        query_job = self.bq_client.client.query(query, job_config=job_config)
        results = query_job.to_dataframe()

        # Validações dos resultados retornados do BigQuery
        self.assertEqual(len(results), 2)

        # Validação de metadados
        self.assertTrue(all(results["_source"] == source_name))
        self.assertTrue(all(results["_execution_id"] == execution_id))
        self.assertTrue(pd.to_datetime(results["_ingested_at"]).notnull().all())

        # Validação de integridade do payload
        aapl_row = results[results["symbol"] == "AAPL"].iloc[0]
        self.assertEqual(aapl_row["totalAssets"], 350000000000.0)
        self.assertEqual(aapl_row["totalLiabilities"], 290000000000.0)
        self.assertEqual(aapl_row["period"], "Q1")

        msft_row = results[results["symbol"] == "MSFT"].iloc[0]
        self.assertEqual(msft_row["totalAssets"], 410000000000.0)
        self.assertEqual(msft_row["netIncome"], 22000000000.0)


if __name__ == "__main__":
    unittest.main()

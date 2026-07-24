import unittest
from unittest.mock import MagicMock

import pandas as pd
from google.cloud import bigquery
from src.services.bronze_service import BronzeService


class TestBronzeService(unittest.TestCase):
    """
    Testes unitários e de integração para o serviço BronzeService.
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
        custom_exec_id = "exec-test-12345"

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


if __name__ == "__main__":
    unittest.main()

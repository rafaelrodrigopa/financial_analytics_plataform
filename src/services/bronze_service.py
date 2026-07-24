import uuid

import pandas as pd
from google.cloud import bigquery
from src.core.config import settings
from src.core.logger import logger
from src.warehouse.bigquery_client import BigQueryClient


class BronzeService:
    """
    Serviço responsável por gerenciar o armazenamento bruto e histórico na Camada Bronze
    da arquitetura Medallion no Google BigQuery.

    Garante:
    - Adição dos campos de auditoria (_ingested_at, _source, _execution_id).
    - Particionamento nativo por data de ingestão (_ingested_at).
    - Clusterização por chaves de negócio (ex: symbol).
    - Carga append-only (WRITE_APPEND) idempotente em lote.
    """

    def __init__(self, bq_client: BigQueryClient | None = None):
        self.bq = bq_client or BigQueryClient()
        self.dataset_id = settings.BRONZE

    def load_dataframe_to_bronze(
        self,
        dataframe: pd.DataFrame,
        table_id: str,
        source: str = "fmp_api",
        execution_id: str | None = None,
        clustering_fields: list[str] | None = None,
    ) -> None:
        """
        Adiciona metadados de auditoria ao DataFrame e realiza a carga em lote (append-only)
        com particionamento por _ingested_at e clusterização na camada Bronze.

        Args:
            dataframe (pd.DataFrame): Dados brutos a serem persistidos na Bronze.
            table_id (str): Nome da tabela no dataset Bronze (ex: 'fmp_balance_sheet').
            source (str): Identificador da origem dos dados (default: 'fmp_api').
            execution_id (str | None): UUID da execução para rastreabilidade de linhagem.
            clustering_fields (list[str] | None): Colunas para clusterização no BigQuery.
        """
        if dataframe is None or dataframe.empty:
            logger.warning(f"DataFrame para a tabela Bronze '{table_id}' está vazio ou Nulo. Carga omitida.")
            return

        df = dataframe.copy()

        # Inclusão dos campos auditáveis
        exec_id = execution_id or str(uuid.uuid4())
        df["_ingested_at"] = pd.Timestamp.now(tz="UTC")
        df["_source"] = source
        df["_execution_id"] = exec_id

        # Configuração de Particionamento Diário por _ingested_at
        time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="_ingested_at",
        )

        # Definição padrão de clusterização se não fornecido
        if clustering_fields is None:
            if "symbol" in df.columns:
                clustering_fields = ["symbol"]
            else:
                clustering_fields = []

        logger.info(
            f"Carregando {len(df)} registros na camada Bronze: '{self.dataset_id}.{table_id}' "
            f"[Execution ID: {exec_id}]..."
        )

        self.bq.upload_dataframe(
            dataframe=df,
            dataset_id=self.dataset_id,
            table_id=table_id,
            write_disposition="WRITE_APPEND",
            time_partitioning=time_partitioning,
            clustering_fields=clustering_fields if clustering_fields else None,
        )

        logger.info(f"Carga na camada Bronze para '{self.dataset_id}.{table_id}' concluída com sucesso.")

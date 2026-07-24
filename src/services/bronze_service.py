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

    def process_landing_to_bronze(
        self,
        tables: list[str] | None = None,
        source: str = "landing_zone",
        execution_id: str | None = None,
    ) -> None:
        """
        Lê todas as tabelas (ou tabelas específicas) da camada Landing, adiciona os campos
        auditáveis (_ingested_at, _source, _execution_id) e as persiste na camada Bronze
        com particionamento diário e clusterização por symbol.

        Args:
            tables (list[str] | None): Lista de nomes das tabelas em Landing a processar.
            source (str): Origem para os campos auditáveis.
            execution_id (str | None): Identificador de execução único.
        """
        if tables is None:
            tables = ["balance_sheet", "cash_flow", "company_profile", "income_statement", "quote"]

        exec_id = execution_id or str(uuid.uuid4())
        logger.info(f"Iniciando promoção de {len(tables)} tabelas de Landing -> Bronze [Execution ID: {exec_id}]")

        for table_id in tables:
            try:
                table_ref = f"{self.bq.project_id}.{settings.LANDING}.{table_id}"
                query = f"SELECT * FROM `{table_ref}`"
                df_landing = self.bq.client.query(query).to_dataframe()

                if df_landing.empty:
                    logger.warning(f"Tabela 'landing.{table_id}' está vazia. Promoção para Bronze omitida.")
                    continue

                bronze_table_id = f"fmp_{table_id}" if not table_id.startswith("fmp_") else table_id

                logger.info(
                    f"Carregando {len(df_landing)} registros de 'landing.{table_id}' para 'bronze.{bronze_table_id}'..."
                )
                self.load_dataframe_to_bronze(
                    dataframe=df_landing,
                    table_id=bronze_table_id,
                    source=source,
                    execution_id=exec_id,
                )
            except Exception as e:
                logger.error(f"Erro ao processar tabela 'landing.{table_id}' para a camada Bronze: {e}")

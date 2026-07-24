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

    def process_landing_to_bronze_sql(
        self,
        tables: list[str] | None = None,
        source: str = "landing_zone",
        execution_id: str | None = None,
    ) -> None:
        """
        Realiza a promoção direta SQL-to-SQL da camada Landing para a camada Bronze no BigQuery.

        Sem tráfego de rede ou conversão em DataFrames Pandas na memória executora,
        executando 100% nativamente dentro do engine de processamento do BigQuery
        com particionamento diário e clusterização por symbol.

        Args:
            tables (list[str] | None): Lista de nomes das tabelas em Landing a processar.
            source (str): Origem para os campos auditáveis.
            execution_id (str | None): Identificador de execução único.
        """
        if tables is None:
            tables = ["balance_sheet", "cash_flow", "company_profile", "income_statement", "quote"]

        self.bq.create_dataset_if_not_exists(self.dataset_id)
        exec_id = execution_id or str(uuid.uuid4())

        logger.info(
            f"Iniciando promoção direta SQL-to-SQL de {len(tables)} tabelas (Landing -> Bronze) "
            f"[Execution ID: {exec_id}]"
        )

        for table_id in tables:
            try:
                landing_table_ref = f"`{self.bq.project_id}.{settings.LANDING}.{table_id}`"
                bronze_table_name = f"fmp_{table_id}" if not table_id.startswith("fmp_") else table_id
                bronze_table_ref = f"`{self.bq.project_id}.{self.dataset_id}.{bronze_table_name}`"

                # 1. Garante a existência da tabela Bronze com DDL particionado e clusterizado caso não exista
                create_ddl = f"""
                CREATE TABLE IF NOT EXISTS {bronze_table_ref}
                PARTITION BY DATE(_ingested_at)
                CLUSTER BY symbol
                AS
                SELECT
                    *,
                    CURRENT_TIMESTAMP() AS _ingested_at,
                    CAST('' AS STRING) AS _source,
                    CAST('' AS STRING) AS _execution_id
                FROM {landing_table_ref}
                WHERE 1=0;
                """
                self.bq.client.query(create_ddl).result()

                # 2. Promove os dados diretamente via SQL INSERT INTO ... SELECT ...
                insert_sql = f"""
                INSERT INTO {bronze_table_ref}
                SELECT
                    *,
                    CURRENT_TIMESTAMP() AS _ingested_at,
                    @source AS _source,
                    @execution_id AS _execution_id
                FROM {landing_table_ref};
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("source", "STRING", source),
                        bigquery.ScalarQueryParameter("execution_id", "STRING", exec_id),
                    ]
                )
                query_job = self.bq.client.query(insert_sql, job_config=job_config)
                query_job.result()  # Aguarda a conclusão do job SQL no BigQuery

                logger.info(
                    f"Promoção SQL-to-SQL concluída para '{bronze_table_ref}'. "
                    f"Linhas inseridas: {query_job.num_dml_affected_rows}"
                )

            except Exception as e:
                if "billingNotEnabled" in str(e) or "DML queries" in str(e):
                    logger.info(
                        f"DML direto requer conta de faturamento (Billing) no GCP. "
                        f"Usando promoção via LoadJob para '{table_id}' [Modo Sandbox/Free Tier OK]..."
                    )
                    self._fallback_load_landing_to_bronze(table_id, source, exec_id)
                else:
                    logger.error(f"Erro na promoção de '{table_id}' para a camada Bronze: {e}")

    def _fallback_load_landing_to_bronze(
        self, table_id: str, source: str = "landing_zone", execution_id: str | None = None
    ) -> None:
        """
        Método de fallback via BigQuery LoadJob para contas GCP sem Faturamento ativado (Free Tier/Sandbox).
        """
        table_ref = f"{self.bq.project_id}.{settings.LANDING}.{table_id}"
        query = f"SELECT * FROM `{table_ref}`"
        df_landing = self.bq.client.query(query).to_dataframe()

        if df_landing.empty:
            logger.warning(f"Tabela 'landing.{table_id}' está vazia. Promoção para Bronze omitida.")
            return

        bronze_table_id = f"fmp_{table_id}" if not table_id.startswith("fmp_") else table_id

        self.load_dataframe_to_bronze(
            dataframe=df_landing,
            table_id=bronze_table_id,
            source=source,
            execution_id=execution_id,
        )

    def process_landing_to_bronze(
        self,
        tables: list[str] | None = None,
        source: str = "landing_zone",
        execution_id: str | None = None,
    ) -> None:
        """
        Interface padrão para promoção de Landing para Bronze.
        Tenta utilizar promoção direta SQL-to-SQL e faz fallback automático para LoadJob caso o projeto esteja no Free Tier.
        """
        self.process_landing_to_bronze_sql(tables=tables, source=source, execution_id=execution_id)

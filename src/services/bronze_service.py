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

    def log_execution_metric(
        self,
        execution_id: str,
        table_name: str,
        rows_read: int,
        rows_written: int,
        started_at: pd.Timestamp,
        ended_at: pd.Timestamp,
        status: str = "SUCCESS",
        error_message: str | None = None,
    ) -> None:
        """
        Registra estatísticas sintéticas de execução de pipeline na tabela de auditoria
        bronze._pipeline_execution_logs no BigQuery.

        Args:
            execution_id (str): UUID único da execução.
            table_name (str): Nome da tabela processada (ex: 'fmp_balance_sheet').
            rows_read (int): Quantidade de registros lidos da Landing Zone.
            rows_written (int): Quantidade de registros salvos na Bronze.
            started_at (pd.Timestamp): Timestamp UTC de início do processamento.
            ended_at (pd.Timestamp): Timestamp UTC de conclusão.
            status (str): Estado final da execução ('SUCCESS', 'WARNING', 'FAILED').
            error_message (str | None): Mensagem de erro caso a execução falhe.
        """
        duration = max((ended_at - started_at).total_seconds(), 0.0)
        log_entry = pd.DataFrame(
            [
                {
                    "execution_id": execution_id,
                    "table_name": table_name,
                    "rows_read": int(rows_read),
                    "rows_written": int(rows_written),
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "duration_seconds": float(duration),
                    "status": status,
                    "error_message": error_message or "",
                }
            ]
        )

        time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="started_at",
        )

        try:
            self.bq.upload_dataframe(
                dataframe=log_entry,
                dataset_id=self.dataset_id,
                table_id="_pipeline_execution_logs",
                write_disposition="WRITE_APPEND",
                time_partitioning=time_partitioning,
                clustering_fields=["status", "table_name"],
            )
            logger.info(
                f"Métrica de observabilidade gravada em '{self.dataset_id}._pipeline_execution_logs' "
                f"[{table_name}: {status}]"
            )
        except Exception as e:
            logger.warning(f"Não foi possível gravar o log de observabilidade no BigQuery: {e}")

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
            started_at = pd.Timestamp.now(tz="UTC")
            bronze_table_name = f"fmp_{table_id}" if not table_id.startswith("fmp_") else table_id
            rows_read = 0
            rows_written = 0

            try:
                landing_table_ref = f"`{self.bq.project_id}.{settings.LANDING}.{table_id}`"
                bronze_table_ref = f"`{self.bq.project_id}.{self.dataset_id}.{bronze_table_name}`"

                # Obtém a contagem de registros na Landing Zone
                count_query = f"SELECT COUNT(1) as cnt FROM {landing_table_ref}"
                count_result = list(self.bq.client.query(count_query).result())
                rows_read = count_result[0]["cnt"] if count_result else 0

                if rows_read == 0:
                    ended_at = pd.Timestamp.now(tz="UTC")
                    logger.warning(f"Tabela 'landing.{table_id}' está vazia. Promoção omitida.")
                    self.log_execution_metric(
                        execution_id=exec_id,
                        table_name=bronze_table_name,
                        rows_read=0,
                        rows_written=0,
                        started_at=started_at,
                        ended_at=ended_at,
                        status="WARNING",
                        error_message="Tabela de origem Landing vazia.",
                    )
                    continue

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
                ended_at = pd.Timestamp.now(tz="UTC")
                rows_written = query_job.num_dml_affected_rows or rows_read

                logger.info(
                    f"Promoção SQL-to-SQL concluída para '{bronze_table_ref}'. Linhas inseridas: {rows_written}"
                )

                self.log_execution_metric(
                    execution_id=exec_id,
                    table_name=bronze_table_name,
                    rows_read=rows_read,
                    rows_written=rows_written,
                    started_at=started_at,
                    ended_at=ended_at,
                    status="SUCCESS",
                )

            except Exception as e:
                ended_at = pd.Timestamp.now(tz="UTC")
                if "billingNotEnabled" in str(e) or "DML queries" in str(e):
                    logger.info(
                        f"DML direto requer conta de faturamento (Billing) no GCP. "
                        f"Usando promoção via LoadJob para '{table_id}' [Modo Sandbox/Free Tier OK]..."
                    )
                    self._fallback_load_landing_to_bronze(
                        table_id, source, exec_id, started_at=started_at, rows_read=rows_read
                    )
                else:
                    logger.error(f"Erro na promoção de '{table_id}' para a camada Bronze: {e}")
                    self.log_execution_metric(
                        execution_id=exec_id,
                        table_name=bronze_table_name,
                        rows_read=rows_read,
                        rows_written=0,
                        started_at=started_at,
                        ended_at=ended_at,
                        status="FAILED",
                        error_message=str(e),
                    )

    def _fallback_load_landing_to_bronze(
        self,
        table_id: str,
        source: str = "landing_zone",
        execution_id: str | None = None,
        started_at: pd.Timestamp | None = None,
        rows_read: int = 0,
    ) -> None:
        """
        Método de fallback via BigQuery LoadJob para contas GCP sem Faturamento ativado (Free Tier/Sandbox).
        """
        start = started_at or pd.Timestamp.now(tz="UTC")
        table_ref = f"{self.bq.project_id}.{settings.LANDING}.{table_id}"
        query = f"SELECT * FROM `{table_ref}`"
        df_landing = self.bq.client.query(query).to_dataframe()

        bronze_table_id = f"fmp_{table_id}" if not table_id.startswith("fmp_") else table_id

        if df_landing.empty:
            ended_at = pd.Timestamp.now(tz="UTC")
            logger.warning(f"Tabela 'landing.{table_id}' está vazia. Promoção para Bronze omitida.")
            self.log_execution_metric(
                execution_id=execution_id or str(uuid.uuid4()),
                table_name=bronze_table_id,
                rows_read=0,
                rows_written=0,
                started_at=start,
                ended_at=ended_at,
                status="WARNING",
                error_message="Tabela de origem Landing vazia.",
            )
            return

        rows_written = len(df_landing)
        read_cnt = rows_read if rows_read > 0 else rows_written

        self.load_dataframe_to_bronze(
            dataframe=df_landing,
            table_id=bronze_table_id,
            source=source,
            execution_id=execution_id,
        )
        ended_at = pd.Timestamp.now(tz="UTC")

        self.log_execution_metric(
            execution_id=execution_id or str(uuid.uuid4()),
            table_name=bronze_table_id,
            rows_read=read_cnt,
            rows_written=rows_written,
            started_at=start,
            ended_at=ended_at,
            status="SUCCESS",
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

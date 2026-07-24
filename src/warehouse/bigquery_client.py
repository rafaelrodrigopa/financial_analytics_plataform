
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from src.core.config import settings
from src.core.exceptions import BigQueryUploadError
from src.core.logger import logger


class BigQueryClient:
    """
    Cliente de integração com o Google BigQuery para gerenciamento de datasets
    e carga de DataFrames nas camadas de dados (Landing, Bronze, Silver, Gold).
    """

    def __init__(self, project_id: str | None = None):
        self.project_id = project_id or settings.PROJECT_ID
        self.client = bigquery.Client(project=self.project_id)

    def list_datasets(self):
        """
        Lista todos os datasets do projeto.
        """
        return list(self.client.list_datasets(project=self.client.project, include_all=True))

    def create_dataset_if_not_exists(self, dataset_id: str, location: str = "US") -> None:
        """
        Garante que o dataset existe no BigQuery, criando-o se necessário.
        """
        dataset_ref = f"{self.project_id}.{dataset_id}"
        try:
            self.client.get_dataset(dataset_ref)
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = location
            self.client.create_dataset(dataset, timeout=30)
            logger.info(f"Dataset '{dataset_ref}' criado com sucesso.")

    def upload_dataframe(
        self, dataframe: pd.DataFrame, dataset_id: str, table_id: str, write_disposition: str = "WRITE_TRUNCATE"
    ) -> None:
        """
        Carrega um DataFrame do Pandas para uma tabela no BigQuery.

        Args:
            dataframe (pd.DataFrame): Dados a serem carregados.
            dataset_id (str): Nome do dataset destino (ex: 'landing').
            table_id (str): Nome da tabela destino (ex: 'income_statement').
            write_disposition (str): Comportamento de escrita ('WRITE_TRUNCATE' ou 'WRITE_APPEND').
        """
        if dataframe is None or dataframe.empty:
            logger.warning(f"DataFrame para '{dataset_id}.{table_id}' está vazio ou Nulo. Carga omitida.")
            return

        # Garante que o dataset existe antes da carga
        self.create_dataset_if_not_exists(dataset_id)

        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"

        disposition_map = {
            "WRITE_TRUNCATE": bigquery.WriteDisposition.WRITE_TRUNCATE,
            "WRITE_APPEND": bigquery.WriteDisposition.WRITE_APPEND,
            "WRITE_EMPTY": bigquery.WriteDisposition.WRITE_EMPTY,
        }

        job_config = bigquery.LoadJobConfig(
            write_disposition=disposition_map.get(write_disposition.upper(), bigquery.WriteDisposition.WRITE_TRUNCATE),
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
        )

        try:
            load_job = self.client.load_table_from_dataframe(dataframe, table_ref, job_config=job_config)
            load_job.result()  # Aguarda a conclusão do job de carga

            destination_table = self.client.get_table(table_ref)
            logger.info(f"Carga concluída para '{table_ref}'. Total de linhas na tabela: {destination_table.num_rows}")
        except Exception as e:
            logger.error(f"Falha no upload para BigQuery '{table_ref}': {e}")
            raise BigQueryUploadError(message=str(e), table_ref=table_ref)

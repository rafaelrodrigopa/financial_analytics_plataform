from google.cloud import bigquery

from src.core.config import settings


class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client(
            project=settings.PROJECT_ID
        )

    def list_datasets(self):
        """
        Lista todos os datasets do projeto.
        """
        return list(self.client.list_datasets(project=self.client.project, include_all=True))
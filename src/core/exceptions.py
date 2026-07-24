class FinancialPlatformError(Exception):
    """
    Exceção base para todos os erros customizados da plataforma financeira.
    """
    pass


class FMPAPIError(FinancialPlatformError):
    """
    Exceção disparada quando ocorre falha de comunicação ou retorno de erro na API FMP.
    """

    def __init__(self, message: str, status_code: int = None, endpoint: str = None):
        self.status_code = status_code
        self.endpoint = endpoint
        details = f" [{endpoint}]" if endpoint else ""
        code_info = f" (Status {status_code})" if status_code else ""
        super().__init__(f"Erro FMP API{details}{code_info}: {message}")


class RateLimitExceededError(FMPAPIError):
    """
    Exceção específica quando a cota diária ou de taxa por minuto da API FMP é atingida (HTTP 429).
    """

    def __init__(self, endpoint: str = None):
        super().__init__(
            message="Limite de requisições excedido. Cota diária/minuto atingida.",
            status_code=429,
            endpoint=endpoint
        )


class BigQueryUploadError(FinancialPlatformError):
    """
    Exceção disparada quando ocorre uma falha na carga de dados ou job no BigQuery.
    """

    def __init__(self, message: str, table_ref: str = None):
        self.table_ref = table_ref
        ref_info = f" Tabela: {table_ref}" if table_ref else ""
        super().__init__(f"Erro de Carga no BigQuery.{ref_info} Detalhes: {message}")

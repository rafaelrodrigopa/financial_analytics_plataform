from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from src.core.logger import logger


class BaseFinancialSchema(BaseModel):
    """
    Schema base para todos os contratos de dados financeiros.
    Garante que symbol e date (quando aplicável) não sejam nulos ou vazios.
    """

    symbol: str = Field(..., min_length=1, description="Símbolo do ativo (ex: MSFT, AAPL)")
    ingested_at: Any | None = None

    class Config:
        extra = "allow"  # Permite campos adicionais retornados pela API FMP sem falhar a validação


class IncomeStatementSchema(BaseFinancialSchema):
    """
    Contrato de dados para o Demonstrativo de Resultado (Income Statement / DRE).
    """

    date: str = Field(..., min_length=4, description="Data de fechamento do relatório (YYYY-MM-DD)")
    revenue: float | None = Field(default=None, description="Receita Total")
    grossProfit: float | None = Field(default=None, description="Lucro Bruto")
    netIncome: float | None = Field(default=None, description="Lucro Líquido")


class BalanceSheetSchema(BaseFinancialSchema):
    """
    Contrato de dados para o Balanço Patrimonial (Balance Sheet).
    """

    date: str = Field(..., min_length=4, description="Data de fechamento do balanço (YYYY-MM-DD)")
    totalAssets: float | None = Field(default=None, description="Ativo Total")
    totalLiabilities: float | None = Field(default=None, description="Passivo Total")
    totalStockholdersEquity: float | None = Field(default=None, description="Patrimônio Líquido")


class CashFlowSchema(BaseFinancialSchema):
    """
    Contrato de dados para a Demonstração dos Fluxos de Caixa (Cash Flow).
    """

    date: str = Field(..., min_length=4, description="Data de fechamento do fluxo de caixa (YYYY-MM-DD)")
    operatingCashFlow: float | None = Field(default=None, description="Fluxo de Caixa Operacional")
    freeCashFlow: float | None = Field(default=None, description="Fluxo de Caixa Livre")


class CompanyProfileSchema(BaseFinancialSchema):
    """
    Contrato de dados para o Perfil Cadastral da Empresa (Company Profile).
    """

    companyName: str | None = Field(default=None, description="Nome da Razão Social")
    industry: str | None = Field(default=None, description="Indústria / Ramo de Atuação")
    sector: str | None = Field(default=None, description="Setor Econômico")


class QuoteSchema(BaseFinancialSchema):
    """
    Contrato de dados para Cotação de Mercado em Tempo Real (Quote).
    """

    price: float | None = Field(default=None, description="Preço de Fechamento / Cotação Atual")


def validate_dataframe(df: pd.DataFrame, schema_cls: type[BaseModel]) -> pd.DataFrame:
    """
    Valida as linhas de um DataFrame do Pandas contra um contrato de schema Pydantic.
    Registra avisos de validação no logger e retorna apenas as linhas em conformidade.

    Args:
        df (pd.DataFrame): DataFrame com os dados brutos da API.
        schema_cls (Type[BaseModel]): Classe do schema Pydantic (ex: IncomeStatementSchema).

    Returns:
        pd.DataFrame: DataFrame validado e em conformidade com o contrato.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    records = df.to_dict(orient="records")
    valid_records: list[dict[str, Any]] = []
    invalid_count = 0

    for idx, record in enumerate(records):
        try:
            # Valida cada dicionário de registro contra a classe Pydantic
            validated_obj = schema_cls(**record)
            # Mantém todos os campos originais convertidos
            valid_records.append(validated_obj.model_dump())
        except ValidationError as err:
            invalid_count += 1
            symbol = record.get("symbol", "UNKNOWN")
            logger.warning(
                f"Linha {idx} ({symbol}) violou o contrato de schema {schema_cls.__name__}: {err.errors()[0].get('msg')}"
            )

    if invalid_count > 0:
        logger.warning(
            f"Validação de Schema {schema_cls.__name__}: {invalid_count} registros inválidos foram ignorados de {len(records)} totais."
        )
    else:
        logger.info(
            f"Validação de Schema {schema_cls.__name__}: 100% dos {len(records)} registros validados com sucesso!"
        )

    return pd.DataFrame(valid_records)

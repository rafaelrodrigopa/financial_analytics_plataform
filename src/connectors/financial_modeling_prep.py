import os
import time
from typing import Optional, Dict, Any
import requests
import pandas as pd

from src.core.config import settings


class FinancialModelingPrep:
    """
    Conector para a API Financial Modeling Prep (FMP).
    Extrai demonstrações financeiras e dados de mercado e os retorna em DataFrames do Pandas.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.FMP_API_KEY
        self.base_url = (base_url or settings.FMP_BASE_URL).rstrip("/")

        if not self.api_key or self.api_key == "sua_chave_api_fmp_aqui":
            raise ValueError(
                "FMP_API_KEY não configurada. Defina a variável no arquivo .env ou passe a chave no construtor."
            )

    def _fetch(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Método auxiliar interno para realizar requisições HTTP GET na API FMP e retornar um DataFrame.
        Inclui mecânica de retry automática em caso de erro 429 (Rate Limit / Too Many Requests).
        """
        params = params or {}
        params["apikey"] = self.api_key

        url = f"{self.base_url}{endpoint}"
        max_retries = 4
        backoff_seconds = 1.5

        for attempt in range(max_retries):
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                if attempt < max_retries - 1:
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue

            response.raise_for_status()
            data = response.json()
            break

        if isinstance(data, dict) and ("Error Message" in data or "error" in data):
            error_msg = data.get("Error Message") or data.get("error")
            raise ValueError(f"Erro na API FMP ({endpoint}): {error_msg}")

        if not data:
            return pd.DataFrame()

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame()

        return df

    def get_income_statement(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        period: str = "annual"
    ) -> pd.DataFrame:
        """
        Extrai a DRE / Demonstrativo de Resultado (Income Statement).
        """
        symbol = symbol or settings.DEFAULT_SYMBOL
        endpoint = settings.FMP_INCOME_STATEMENT_ENDPOINT
        params = {"symbol": symbol, "limit": limit, "period": period}

        df = self._fetch(endpoint, params=params)
        if not df.empty and "symbol" not in df.columns:
            df["symbol"] = symbol
        return df

    def get_balance_sheet(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        period: str = "annual"
    ) -> pd.DataFrame:
        """
        Extrai o Balanço Patrimonial (Balance Sheet Statement).
        """
        symbol = symbol or settings.DEFAULT_SYMBOL
        endpoint = settings.FMP_BALANCE_SHEET_ENDPOINT
        params = {"symbol": symbol, "limit": limit, "period": period}

        df = self._fetch(endpoint, params=params)
        if not df.empty and "symbol" not in df.columns:
            df["symbol"] = symbol
        return df

    def get_cash_flow(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        period: str = "annual"
    ) -> pd.DataFrame:
        """
        Extrai a Demonstração dos Fluxos de Caixa (Cash Flow Statement).
        """
        symbol = symbol or settings.DEFAULT_SYMBOL
        endpoint = settings.FMP_CASH_FLOW_ENDPOINT
        params = {"symbol": symbol, "limit": limit, "period": period}

        df = self._fetch(endpoint, params=params)
        if not df.empty and "symbol" not in df.columns:
            df["symbol"] = symbol
        return df

    def get_company_profile(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        Extrai o perfil e dados cadastrais da empresa (Company Profile).
        """
        symbol = symbol or settings.DEFAULT_SYMBOL
        endpoint = settings.FMP_PROFILE_ENDPOINT
        params = {"symbol": symbol}

        df = self._fetch(endpoint, params=params)
        if not df.empty and "symbol" not in df.columns:
            df["symbol"] = symbol
        return df

    def get_quote(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        Extrai cotação / dados de mercado em tempo real (Quote).
        """
        symbol = symbol or settings.DEFAULT_SYMBOL
        endpoint = settings.FMP_QUOTE_ENDPOINT
        params = {"symbol": symbol}

        df = self._fetch(endpoint, params=params)
        if not df.empty and "symbol" not in df.columns:
            df["symbol"] = symbol
        return df

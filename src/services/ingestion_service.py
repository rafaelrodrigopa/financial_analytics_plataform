from typing import List, Optional
import time
import pandas as pd

from src.connectors import FinancialModelingPrep
from src.warehouse.bigquery_client import BigQueryClient
from src.core.config import settings
from src.core.logger import logger


DEFAULT_BATCH_24_SYMBOLS = [
    # Top 24 Leaders (Tech, Semiconductors, Financials & Retail)
    "MSFT", "AAPL", "GOOGL", "AMZN", "META", "ORCL", "CRM", "ADBE", "NOW", "INTU",
    "IBM", "SAP", "ACN", "UBER", "NVDA", "AMD", "INTC", "QCOM", "JPM", "V",
    "MA", "BAC", "WMT", "COST"
]

ALL_TOP_100_SYMBOLS = [
    # Tech & Software
    "MSFT", "AAPL", "GOOGL", "AMZN", "META", "ORCL", "CRM", "ADBE", "NOW", "INTU",
    "IBM", "SAP", "ACN", "UBER", "PANW", "SNOW", "PLTR", "SHOP", "SQ", "ABNB",

    # Semiconductors
    "NVDA", "AMD", "INTC", "AVGO", "QCOM", "TSM", "TXN", "MU", "AMAT", "LRCX",

    # Financials & Payments
    "JPM", "V", "MA", "BAC", "WFC", "C", "MS", "GS", "BLK", "AXP",
    "PYPL", "SCHW", "PNC", "USB",

    # Consumer & Retail
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "MCD", "SBUX", "KO", "PEP",
    "PG", "CL", "PM", "MO", "EL",

    # Healthcare & Pharma
    "PFE", "ABBV", "JNJ", "UNH", "LLY", "MRK", "TMO", "ABT", "AMGN", "DHR",
    "BMY", "CVS", "GILD", "ISRG", "VRTX",

    # Industrials & Defense
    "GE", "CAT", "BA", "HON", "UNP", "LMT", "RTX", "DE", "MMM", "UPS",

    # Energy & Materials
    "XOM", "CVX", "COP", "SLB", "EOG", "LIN", "APD", "FCX", "NEM", "VALE",

    # Media & Telecom
    "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "WBD",

    # Automotive & Mobility
    "TSLA", "F", "GM", "RACE", "TM"
]


class IngestionService:
    """
    Serviço responsável por orquestrar a extração de dados de múltiplos símbolos
    nas APIs e realizar a carga agregada na camada Landing do BigQuery.
    """

    def __init__(self, symbols: Optional[List[str]] = None):
        self.symbols = symbols or DEFAULT_BATCH_24_SYMBOLS
        self.fmp = FinancialModelingPrep()
        self.bq = BigQueryClient()

    def run_landing_ingestion(self, limit_statements: int = 5) -> None:
        """
        Executa a ingestão completa de todos os símbolos configurados e envia os
        dados combinados para o dataset Landing no BigQuery.
        """
        total_symbols = len(self.symbols)
        logger.info(f"Iniciando ingestão de {total_symbols} empresas para a camada Landing (Dataset: '{settings.LANDING}')")

        quotes_list = []
        profiles_list = []
        incomes_list = []
        balances_list = []
        cash_flows_list = []

        for idx, symbol in enumerate(self.symbols, 1):
            logger.info(f"[{idx}/{total_symbols}] Extraindo dados para {symbol}...")
            try:
                # Quote
                df_q = self.fmp.get_quote(symbol)
                if not df_q.empty:
                    quotes_list.append(df_q)

                # Profile
                df_p = self.fmp.get_company_profile(symbol)
                if not df_p.empty:
                    profiles_list.append(df_p)

                # Income Statement
                df_i = self.fmp.get_income_statement(symbol, limit=limit_statements)
                if not df_i.empty:
                    incomes_list.append(df_i)

                # Balance Sheet
                df_b = self.fmp.get_balance_sheet(symbol, limit=limit_statements)
                if not df_b.empty:
                    balances_list.append(df_b)

                # Cash Flow
                df_c = self.fmp.get_cash_flow(symbol, limit=limit_statements)
                if not df_c.empty:
                    cash_flows_list.append(df_c)

                # Pequena pausa entre cada empresa para evitar estouro do Rate Limit (Erro 429)
                time.sleep(0.15)

            except Exception as e:
                logger.warning(f"Erro ao extrair dados para {symbol}: {e}")

        # Combina os DataFrames de todos os símbolos e faz o upload para o BigQuery
        logger.info("Iniciando Upload Combinado para a Camada Landing do BigQuery...")
        self._upload_combined(quotes_list, "quote")
        self._upload_combined(profiles_list, "company_profile")
        self._upload_combined(incomes_list, "income_statement")
        self._upload_combined(balances_list, "balance_sheet")
        self._upload_combined(cash_flows_list, "cash_flow")

        logger.info("Processo de ingestão para a camada Landing finalizado com sucesso!")

    def _upload_combined(self, df_list: List[pd.DataFrame], table_id: str) -> None:
        """
        Concatena os DataFrames de cada símbolo, adiciona a coluna de auditoria ingested_at
        e faz o upload para a tabela Landing correspondente.
        """
        if not df_list:
            logger.warning(f"Nenhum dado encontrado para a tabela '{table_id}'. Carga omitida.")
            return

        combined_df = pd.concat(df_list, ignore_index=True)
        # Adiciona a data/hora UTC do lote de ingestão para auditoria
        combined_df["ingested_at"] = pd.Timestamp.now(tz="UTC")

        logger.info(f"Carregando {len(combined_df)} registros (com 'ingested_at') na tabela 'landing.{table_id}'...")

        self.bq.upload_dataframe(
            dataframe=combined_df,
            dataset_id=settings.LANDING,
            table_id=table_id,
            write_disposition="WRITE_TRUNCATE"
        )

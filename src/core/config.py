from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    LANDING = os.getenv("BQ_DATASET_LANDING")
    BRONZE = os.getenv("BQ_DATASET_BRONZE")
    SILVER = os.getenv("BQ_DATASET_SILVER")
    GOLD = os.getenv("BQ_DATASET_GOLD")
    FMP_API_KEY = os.getenv("FMP_API_KEY")
    FMP_BASE_URL = os.getenv("FMP_BASE_URL", "https://financialmodelingprep.com/stable")
    FMP_INCOME_STATEMENT_ENDPOINT = os.getenv("FMP_INCOME_STATEMENT_ENDPOINT", "/income-statement")
    FMP_BALANCE_SHEET_ENDPOINT = os.getenv("FMP_BALANCE_SHEET_ENDPOINT", "/balance-sheet-statement")
    FMP_CASH_FLOW_ENDPOINT = os.getenv("FMP_CASH_FLOW_ENDPOINT", "/cash-flow-statement")
    FMP_PROFILE_ENDPOINT = os.getenv("FMP_PROFILE_ENDPOINT", "/profile")
    FMP_QUOTE_ENDPOINT = os.getenv("FMP_QUOTE_ENDPOINT", "/quote")
    DEFAULT_SYMBOL = os.getenv("DEFAULT_SYMBOL", "MSFT")

settings = Settings()
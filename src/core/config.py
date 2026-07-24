from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_PROJECT_ID = PROJECT_ID
    LANDING = os.getenv("BQ_DATASET_LANDING")
    BRONZE = os.getenv("BQ_DATASET_BRONZE")
    SILVER = os.getenv("BQ_DATASET_SILVER")
    GOLD = os.getenv("BQ_DATASET_GOLD")
    FMP_API_KEY = os.getenv("FMP_API_KEY")

settings = Settings()
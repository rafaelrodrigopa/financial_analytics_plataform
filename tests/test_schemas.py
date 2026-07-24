import os
import sys

import pandas as pd

# Adiciona a raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas import IncomeStatementSchema, validate_dataframe


def test_schema_validation():
    print("--- Testando Validador de Schema Pydantic ---")

    # DataFrame de teste com dados válidos e um registro inválido (symbol nulo/vazio)
    sample_data = [
        {"symbol": "MSFT", "date": "2025-06-30", "revenue": 281724000000.0, "netIncome": 101832000000.0},
        {"symbol": "AAPL", "date": "2024-09-28", "revenue": 391035000000.0, "netIncome": 93736000000.0},
        {"symbol": "", "date": "2024-01-01", "revenue": 100.0, "netIncome": 10.0},  # Inválido: symbol vazio
    ]

    df_sample = pd.DataFrame(sample_data)
    print(f"Total de registros de teste de entrada: {len(df_sample)}")

    df_validated = validate_dataframe(df_sample, IncomeStatementSchema)

    print(f"Total de registros aprovados pela validação Pydantic: {len(df_validated)}")
    assert len(df_validated) == 2, "Deveria aprovar exatamente 2 registros válidos"
    assert "MSFT" in df_validated["symbol"].values
    assert "AAPL" in df_validated["symbol"].values

    print("\n[OK] Teste de Validacao de Schemas Pydantic concluido com sucesso!")


if __name__ == "__main__":
    test_schema_validation()

import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.connectors.financial_modeling_prep import FinancialModelingPrep
from src.core.config import settings


def test_fmp_connector():
    """
    Testa a inicialização e extração de dados do conector FinancialModelingPrep.
    """
    print(f"Base URL: {settings.FMP_BASE_URL}")
    print(f"Símbolo padrão: {settings.DEFAULT_SYMBOL}")

    fmp = FinancialModelingPrep()

    print("\n--- Testando Quote ---")
    df_quote = fmp.get_quote()
    assert not df_quote.empty, "DataFrame de Quote não deve estar vazio"
    print(f"Quote retornado ({len(df_quote)} linhas):")
    print(df_quote[["symbol", "name", "price"]].to_string(index=False))

    print("\n--- Testando Profile ---")
    df_profile = fmp.get_company_profile()
    assert not df_profile.empty, "DataFrame de Profile não deve estar vazio"
    print(f"Profile retornado ({len(df_profile)} linhas): {df_profile.columns.tolist()[:5]}")

    print("\n--- Testando Income Statement ---")
    df_income = fmp.get_income_statement(limit=2)
    assert not df_income.empty, "DataFrame de Income Statement não deve estar vazio"
    print(f"Income Statement retornado ({len(df_income)} linhas)")

    print("\n--- Testando Balance Sheet ---")
    df_balance = fmp.get_balance_sheet(limit=2)
    assert not df_balance.empty, "DataFrame de Balance Sheet não deve estar vazio"
    print(f"Balance Sheet retornado ({len(df_balance)} linhas)")

    print("\n--- Testando Cash Flow ---")
    df_cash = fmp.get_cash_flow(limit=2)
    assert not df_cash.empty, "DataFrame de Cash Flow não deve estar vazio"
    print(f"Cash Flow retornado ({len(df_cash)} linhas)")

    print("\nTodos os métodos do conector FMP funcionaram com sucesso!")


if __name__ == "__main__":
    test_fmp_connector()

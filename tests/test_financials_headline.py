import pandas as pd

from edgar_research.commands import financials as fin


class _Stmt:
    def __init__(self, df):
        self._df = df

    def to_dataframe(self):
        return self._df


def test_is_headline_excludes_abstract_and_dimensional():
    base = {"abstract": False, "dimension": False, "is_breakdown": False}
    assert fin._is_headline(pd.Series(base)) is True
    assert fin._is_headline(pd.Series({**base, "abstract": True})) is False
    assert fin._is_headline(pd.Series({**base, "dimension": True})) is False
    assert fin._is_headline(pd.Series({**base, "is_breakdown": True})) is False
    # a NaN in a bool column must not crash or be misread as "excluded"
    assert fin._is_headline(pd.Series({**base, "dimension": float("nan")})) is True


def test_statement_records_compact_drops_noise_and_annotates_canonical():
    df = pd.DataFrame([
        {"concept": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
         "label": "Net sales", "abstract": False, "dimension": False, "is_breakdown": False,
         "2025 (FY)": 100.0, "2024 (FY)": 90.0},
        {"concept": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
         "label": "Americas", "abstract": False, "dimension": True, "is_breakdown": True,
         "2025 (FY)": 40.0, "2024 (FY)": 35.0},          # dimensional -> dropped
        {"concept": "us-gaap_StatementHeader", "label": "Revenue:",
         "abstract": True, "dimension": False, "is_breakdown": False,
         "2025 (FY)": None, "2024 (FY)": None},          # abstract/all-null -> dropped
    ])
    rows, period_cols = fin._statement_records(_Stmt(df), periods=2, full=False)
    assert period_cols == ["2025 (FY)", "2024 (FY)"]
    assert len(rows) == 1
    assert rows[0]["label"] == "Net sales"
    assert rows[0]["concept"] == "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax"
    assert rows[0]["canonical"] == "revenue"
    assert rows[0]["2025 (FY)"] == 100.0


def test_statement_records_full_keeps_dimensional_rows():
    df = pd.DataFrame([
        {"concept": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
         "label": "Net sales", "abstract": False, "dimension": False, "is_breakdown": False,
         "2025 (FY)": 100.0},
        {"concept": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
         "label": "Americas", "abstract": False, "dimension": True, "is_breakdown": True,
         "2025 (FY)": 40.0},
    ])
    rows, _ = fin._statement_records(_Stmt(df), periods=1, full=True)
    assert len(rows) == 2

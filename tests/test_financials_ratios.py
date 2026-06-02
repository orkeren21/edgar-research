import pandas as pd

from edgar_research.commands import financials as fin


def test_safe_div():
    assert fin._safe_div(10, 2) == 5
    assert fin._safe_div(10, 0) is None
    assert fin._safe_div(None, 2) is None
    assert fin._safe_div(10, None) is None


def test_val_indexing():
    assert fin._val({"revenue": [1.0, 2.0]}, "revenue", 0) == 1.0
    assert fin._val({"revenue": [1.0]}, "revenue", 5) is None
    assert fin._val({}, "revenue", 0) is None


def test_period_key_strips_fy_suffix():
    assert fin._period_key("2025-09-27 (FY)") == "2025-09-27"
    assert fin._period_key("2025-09-27") == "2025-09-27"


def test_canonical_ordered_headline_first_match():
    df = pd.DataFrame([
        {"concept": "us-gaap_Revenues", "abstract": False, "dimension": False,
         "is_breakdown": False, "2025 (FY)": 100.0, "2024 (FY)": 90.0},
        {"concept": "us-gaap_Revenues", "abstract": False, "dimension": True,
         "is_breakdown": True, "2025 (FY)": 40.0, "2024 (FY)": 35.0},   # dimensional dup -> ignored
        {"concept": "us-gaap_NetIncomeLoss", "abstract": False, "dimension": False,
         "is_breakdown": False, "2025 (FY)": 20.0, "2024 (FY)": 18.0},
    ])
    period_cols, series = fin._canonical_ordered(df)
    assert period_cols == ["2025 (FY)", "2024 (FY)"]
    assert series["revenue"] == [100.0, 90.0]
    assert series["net_income"] == [20.0, 18.0]


def test_canonical_ordered_no_concept_column():
    assert fin._canonical_ordered(pd.DataFrame({"x": [1]})) == ([], {})


def test_ratios_from_series_per_period_identity_and_growth():
    periods = ["2025 (FY)", "2024 (FY)"]
    inc = {
        "revenue": [1000.0, 800.0],
        "net_income": [200.0, 120.0],
        "operating_income": [300.0, 200.0],
        "gross_profit": [500.0, 400.0],
    }
    bal = {
        "total_assets": {"2025": 4000.0, "2024": 3500.0},
        "stockholders_equity": {"2025": 1500.0, "2024": 1400.0},
        "current_assets": {"2025": 800.0, "2024": 700.0},
        "current_liabilities": {"2025": 400.0, "2024": 350.0},
    }
    cf = {
        "operating_cash_flow": {"2025": 350.0, "2024": 250.0},
        "capital_expenditures": {"2025": 50.0, "2024": 40.0},
    }
    out = fin._ratios_from_series(periods, inc, bal, cf, periods=2)
    assert [r["period"] for r in out] == periods
    p0 = out[0]
    assert p0["gross_margin"] == 0.5
    assert p0["operating_margin"] == 0.3
    assert p0["net_margin"] == 0.2
    assert p0["debt_to_assets"] == (4000.0 - 1500.0) / 4000.0
    assert p0["debt_to_equity"] == (4000.0 - 1500.0) / 1500.0
    assert p0["current_ratio"] == 2.0
    assert p0["fcf_margin"] == (350.0 - 50.0) / 1000.0
    assert p0["revenue_growth"] == (1000.0 - 800.0) / 800.0
    assert "revenue_growth" not in out[1]


def test_ratios_align_balance_by_period_key_not_index():
    # balance keyed by fiscal date, deliberately in reversed insertion order:
    # alignment must be by date key, not list position.
    inc_periods = ["2025-09-27 (FY)", "2024-09-28 (FY)"]
    inc = {"revenue": [1000.0, 900.0], "net_income": [200.0, 150.0]}
    bal = {"stockholders_equity": {"2024-09-28": 1000.0, "2025-09-27": 1500.0}}
    out = fin._ratios_from_series(inc_periods, inc, bal, {}, periods=2)
    assert out[0]["return_on_equity"] == 200.0 / 1500.0   # 2025 income <-> 2025 equity
    assert out[1]["return_on_equity"] == 150.0 / 1000.0   # 2024 income <-> 2024 equity


def test_ratios_from_series_omits_missing_inputs():
    out = fin._ratios_from_series(["2025 (FY)"], {"net_income": [100.0]}, {}, {}, periods=1)
    assert out == [{"period": "2025 (FY)"}]

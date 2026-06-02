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


def test_ratios_from_series_per_period_identity_and_growth():
    periods = ["2025 (FY)", "2024 (FY)"]
    inc = {
        "revenue": [1000.0, 800.0],
        "net_income": [200.0, 120.0],
        "operating_income": [300.0, 200.0],
        "gross_profit": [500.0, 400.0],
    }
    bal = {
        "total_assets": [4000.0, 3500.0],
        "stockholders_equity": [1500.0, 1400.0],
        "current_assets": [800.0, 700.0],
        "current_liabilities": [400.0, 350.0],
    }
    cf = {"operating_cash_flow": [350.0, 250.0], "capital_expenditures": [50.0, 40.0]}

    out = fin._ratios_from_series(periods, inc, bal, cf, periods=2)
    assert [r["period"] for r in out] == periods
    p0 = out[0]
    assert p0["gross_margin"] == 0.5
    assert p0["operating_margin"] == 0.3
    assert p0["net_margin"] == 0.2
    assert p0["debt_to_assets"] == (4000.0 - 1500.0) / 4000.0   # identity, not tagged liabilities
    assert p0["debt_to_equity"] == (4000.0 - 1500.0) / 1500.0
    assert p0["current_ratio"] == 2.0
    assert p0["fcf_margin"] == (350.0 - 50.0) / 1000.0
    assert p0["revenue_growth"] == (1000.0 - 800.0) / 800.0
    assert "revenue_growth" not in out[1]            # oldest period has no prior


def test_ratios_from_series_omits_missing_inputs():
    out = fin._ratios_from_series(["2025 (FY)"], {"net_income": [100.0]}, {}, {}, periods=1)
    assert out == [{"period": "2025 (FY)"}]

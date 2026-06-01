import pandas as pd

from edgar_research.commands import financials as fin


def test_safe_div():
    assert fin._safe_div(10, 2) == 5
    assert fin._safe_div(10, 0) is None
    assert fin._safe_div(None, 2) is None
    assert fin._safe_div(10, None) is None


def test_ratios_from_metrics_computes_and_omits_missing():
    metrics = {
        "revenue": 1000.0,
        "net_income": 200.0,
        "operating_income": 300.0,
        "total_assets": 4000.0,
        "total_liabilities": 2500.0,
        "stockholders_equity": 1500.0,
        "current_assets": 800.0,
        "current_liabilities": 400.0,
        "free_cash_flow": None,  # missing input -> fcf_margin omitted
    }
    r = fin._ratios_from_metrics(metrics)
    assert r["operating_margin"] == 0.3
    assert r["net_margin"] == 0.2
    assert r["return_on_equity"] == 200.0 / 1500.0
    assert r["return_on_assets"] == 0.05
    assert r["current_ratio"] == 2.0
    assert r["debt_to_equity"] == 2500.0 / 1500.0
    assert r["debt_to_assets"] == 0.625
    assert "fcf_margin" not in r


def test_ratios_uses_accounting_identity_for_liabilities():
    # edgartools sometimes mis-tags total_liabilities as == total_assets; we derive
    # liabilities = assets - equity instead, so debt_to_assets isn't a bogus 1.0.
    metrics = {
        "revenue": 1000.0,
        "net_income": 100.0,
        "total_assets": 4000.0,
        "stockholders_equity": 1500.0,
        "total_liabilities": 4000.0,  # mis-tagged (equals total_assets)
    }
    r = fin._ratios_from_metrics(metrics)
    assert r["debt_to_assets"] == 0.625          # (4000 - 1500) / 4000, not 1.0
    assert r["debt_to_equity"] == 2500.0 / 1500.0


def test_ratios_from_metrics_empty_without_inputs():
    r = fin._ratios_from_metrics({"net_income": 100.0})
    assert r == {}


def test_latest_two_revenue():
    df = pd.DataFrame({
        "concept": ["us-gaap_Revenues", "us-gaap_NetIncomeLoss"],
        "label": ["Revenue", "Net income"],
        "2025 (FY)": [1100.0, 200.0],
        "2024 (FY)": [1000.0, 150.0],
    })
    assert fin._latest_two_revenue(df) == (1100.0, 1000.0)


def test_latest_two_revenue_missing_concept():
    df = pd.DataFrame({
        "concept": ["us-gaap_NetIncomeLoss"],
        "label": ["Net income"],
        "2025 (FY)": [200.0],
        "2024 (FY)": [150.0],
    })
    assert fin._latest_two_revenue(df) == (None, None)

from edgar_research.concepts import canonical_for


def test_canonical_for_gaap():
    assert canonical_for("us-gaap_NetIncomeLoss") == "net_income"
    assert canonical_for("us-gaap_Assets") == "total_assets"
    assert canonical_for("us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax") == "revenue"


def test_canonical_for_ifrs():
    assert canonical_for("ifrs-full_ProfitLoss") == "net_income"
    assert canonical_for("ifrs-full_Revenue") == "revenue"


def test_canonical_for_unmapped_and_none():
    assert canonical_for("us-gaap_SomethingObscure") is None
    assert canonical_for(None) is None
    assert canonical_for("") is None

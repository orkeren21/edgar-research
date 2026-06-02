"""Canonical mapping of headline XBRL concepts (US-GAAP and IFRS) to common names."""
from __future__ import annotations

# canonical name -> source concepts (us-gaap_* and ifrs-full_*) that mean the same thing.
_CANONICAL_SOURCES: dict[str, tuple[str, ...]] = {
    "revenue": (
        "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax",
        "us-gaap_Revenues",
        "us-gaap_SalesRevenueNet",
        "ifrs-full_Revenue",
    ),
    "cost_of_revenue": (
        "us-gaap_CostOfGoodsAndServicesSold",
        "us-gaap_CostOfRevenue",
        "ifrs-full_CostOfSales",
    ),
    "gross_profit": ("us-gaap_GrossProfit", "ifrs-full_GrossProfit"),
    "operating_income": (
        "us-gaap_OperatingIncomeLoss",
        "ifrs-full_ProfitLossFromOperatingActivities",
    ),
    "operating_expenses": ("us-gaap_OperatingExpenses", "ifrs-full_OperatingExpense"),
    "research_and_development": (
        "us-gaap_ResearchAndDevelopmentExpense",
        "ifrs-full_ResearchAndDevelopmentExpense",
    ),
    "net_income": ("us-gaap_NetIncomeLoss", "us-gaap_ProfitLoss", "ifrs-full_ProfitLoss"),
    "total_assets": ("us-gaap_Assets", "ifrs-full_Assets"),
    "total_liabilities": ("us-gaap_Liabilities", "ifrs-full_Liabilities"),
    "stockholders_equity": (
        "us-gaap_StockholdersEquity",
        "us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "ifrs-full_Equity",
    ),
    "current_assets": ("us-gaap_AssetsCurrent", "ifrs-full_CurrentAssets"),
    "current_liabilities": ("us-gaap_LiabilitiesCurrent", "ifrs-full_CurrentLiabilities"),
    "operating_cash_flow": (
        "us-gaap_NetCashProvidedByUsedInOperatingActivities",
        "us-gaap_NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "ifrs-full_CashFlowsFromUsedInOperatingActivities",
    ),
    "capital_expenditures": (
        "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
        "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
    ),
    "eps_basic": ("us-gaap_EarningsPerShareBasic", "ifrs-full_BasicEarningsLossPerShare"),
    "eps_diluted": ("us-gaap_EarningsPerShareDiluted", "ifrs-full_DilutedEarningsLossPerShare"),
}

# Inverted: concept -> canonical name.
_CONCEPT_TO_CANONICAL: dict[str, str] = {
    concept: name
    for name, concepts in _CANONICAL_SOURCES.items()
    for concept in concepts
}


def canonical_for(concept: str | None) -> str | None:
    """Canonical name for an XBRL concept, or None if unmapped/empty."""
    if not concept:
        return None
    return _CONCEPT_TO_CANONICAL.get(concept)

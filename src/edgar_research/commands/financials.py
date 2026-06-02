import pandas as pd
from edgar import Company

from .. import output
from ..concepts import canonical_for

# Columns in a Statement.to_dataframe() that describe the row, not a period value.
_METADATA_COLS = {
    "concept", "label", "standard_concept", "level", "abstract", "dimension",
    "is_breakdown", "dimension_axis", "dimension_member", "dimension_member_label",
    "dimension_label", "balance", "weight", "preferred_sign",
    "parent_concept", "parent_abstract_concept",
}

_STATEMENTS = {
    "income": "income_statement",
    "balance": "balance_sheet",
    "cashflow": "cash_flow_statement",
}


def _period_columns(df):
    return [c for c in df.columns if c not in _METADATA_COLS]


def _is_headline(row) -> bool:
    """True for a real line item (not an abstract header or dimensional breakdown)."""
    for col in ("abstract", "dimension", "is_breakdown"):
        if col in row and not pd.isna(row[col]) and row[col]:
            return False
    return True


def _statement_records(stmt, periods, full=False):
    df = stmt.to_dataframe()
    period_cols = _period_columns(df)[:periods]
    rows = []
    for _, row in df.iterrows():
        if not full and not _is_headline(row):
            continue
        values = {p: output.sanitize(row[p]) for p in period_cols}
        if all(v is None for v in values.values()):
            continue
        rec = {
            "label": output.sanitize(row.get("label")),
            "concept": output.sanitize(row.get("concept")),
            "canonical": canonical_for(row.get("concept")),
        }
        rec.update(values)
        rows.append(rec)
    return rows, period_cols


def _statement_markdown(stmt, rows, full):
    """Markdown for a statement. ``rows`` is used only in compact mode; full mode
    re-renders the complete edgartools frame."""
    return stmt.to_markdown() if full else output.records_to_markdown(rows)


_REVENUE_CONCEPTS = (
    "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax",
    "us-gaap_Revenues",
    "us-gaap_SalesRevenueNet",
)


def _safe_div(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _ratios_from_metrics(metrics: dict) -> dict:
    """Latest-period ratios derived from edgartools' financial metrics.

    Any ratio whose inputs are missing is omitted (not emitted as null), so the
    output contains only what could actually be computed.
    """
    m = metrics or {}
    revenue = m.get("revenue")
    net_income = m.get("net_income")
    operating_income = m.get("operating_income")
    total_assets = m.get("total_assets")
    equity = m.get("stockholders_equity")
    # Prefer the accounting identity for liabilities (Assets - Equity): edgartools'
    # total_liabilities metric sometimes mis-tags to LiabilitiesAndStockholdersEquity
    # (which equals total assets), producing a bogus debt_to_assets of 1.0.
    if total_assets is not None and equity is not None:
        total_liabilities = total_assets - equity
    else:
        total_liabilities = m.get("total_liabilities")
    candidates = {
        "operating_margin": _safe_div(operating_income, revenue),
        "net_margin": _safe_div(net_income, revenue),
        "return_on_equity": _safe_div(net_income, equity),
        "return_on_assets": _safe_div(net_income, total_assets),
        "current_ratio": _safe_div(m.get("current_assets"), m.get("current_liabilities")),
        "debt_to_equity": _safe_div(total_liabilities, equity),
        "debt_to_assets": _safe_div(total_liabilities, total_assets),
        "fcf_margin": _safe_div(m.get("free_cash_flow"), revenue),
    }
    return {name: value for name, value in candidates.items() if value is not None}


def _latest_two_revenue(income_df):
    """(latest, prior) revenue from an income-statement dataframe, else (None, None)."""
    if "concept" not in income_df.columns:
        return (None, None)
    period_cols = [c for c in income_df.columns if c not in _METADATA_COLS]
    if len(period_cols) < 2:
        return (None, None)
    for concept in _REVENUE_CONCEPTS:
        match = income_df[income_df["concept"] == concept]
        if not match.empty:
            row = match.iloc[0]
            return (output.sanitize(row[period_cols[0]]), output.sanitize(row[period_cols[1]]))
    return (None, None)


def _compute_ratios(fin) -> dict:
    """Latest-period ratios (margins, returns, leverage) + revenue YoY growth."""
    ratios = _ratios_from_metrics(fin.get_financial_metrics())
    try:
        latest, prior = _latest_two_revenue(fin.income_statement().to_dataframe())
        if latest is not None and prior not in (None, 0):
            ratios["revenue_growth"] = (latest - prior) / prior
    except Exception:
        pass  # growth is best-effort; omit if the income statement can't be read
    return ratios


def run(args):
    c = Company(args.ticker)
    fin = c.get_financials()
    wanted = list(_STATEMENTS) if args.statement == "all" else [args.statement]
    data = {}
    md_parts = []
    for key in wanted:
        stmt = getattr(fin, _STATEMENTS[key])()
        rows, period_cols = _statement_records(stmt, args.periods, full=args.full)
        data[key] = {"periods": period_cols, "rows": rows}
        md_parts.append(f"## {key.title()} statement\n\n" + _statement_markdown(stmt, rows, args.full))
    if args.ratios:
        data["ratios"] = _compute_ratios(fin)
    payload = output.success(
        "financials",
        {"ticker": args.ticker, "statement": args.statement,
         "periods": args.periods, "ratios": args.ratios, "full": args.full},
        data,
    )
    return payload, "\n\n".join(md_parts)

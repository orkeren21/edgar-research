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


def _safe_div(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _canonical_ordered(df):
    """(period_labels, {canonical_name: [values aligned to period_labels]}).

    Reads only headline rows; the first match per canonical name wins (the headline
    line, not a dimensional duplicate sharing the same concept).
    """
    if "concept" not in df.columns:
        return [], {}
    period_cols = _period_columns(df)
    series = {}
    for _, row in df.iterrows():
        if not _is_headline(row):
            continue
        name = canonical_for(row.get("concept"))
        if name is None or name in series:
            continue
        series[name] = [output.sanitize(row[p]) for p in period_cols]
    return period_cols, series


def _val(series, name, i):
    vals = series.get(name)
    if vals is None or i >= len(vals):
        return None
    return vals[i]


def _ratios_from_series(inc_periods, inc, bal, cf, periods):
    """Pure per-period ratios from ordered canonical series (newest-first)."""
    n = min(len(inc_periods), periods) if inc_periods else 0
    result = []
    for i in range(n):
        revenue = _val(inc, "revenue", i)
        net_income = _val(inc, "net_income", i)
        operating_income = _val(inc, "operating_income", i)
        gross_profit = _val(inc, "gross_profit", i)
        total_assets = _val(bal, "total_assets", i)
        equity = _val(bal, "stockholders_equity", i)
        current_assets = _val(bal, "current_assets", i)
        current_liabilities = _val(bal, "current_liabilities", i)
        ocf = _val(cf, "operating_cash_flow", i)
        capex = _val(cf, "capital_expenditures", i)
        # Liabilities via the accounting identity (Assets - Equity); edgartools' tagged
        # total_liabilities can mis-map to LiabilitiesAndStockholdersEquity (== assets).
        liabilities = (total_assets - equity) if (total_assets is not None and equity is not None) else None
        fcf = (ocf - capex) if (ocf is not None and capex is not None) else None
        prior_revenue = _val(inc, "revenue", i + 1)
        revenue_growth = (
            (revenue - prior_revenue) / prior_revenue
            if (revenue is not None and prior_revenue not in (None, 0)) else None
        )
        candidates = {
            "gross_margin": _safe_div(gross_profit, revenue),
            "operating_margin": _safe_div(operating_income, revenue),
            "net_margin": _safe_div(net_income, revenue),
            "return_on_equity": _safe_div(net_income, equity),
            "return_on_assets": _safe_div(net_income, total_assets),
            "current_ratio": _safe_div(current_assets, current_liabilities),
            "debt_to_equity": _safe_div(liabilities, equity),
            "debt_to_assets": _safe_div(liabilities, total_assets),
            "fcf_margin": _safe_div(fcf, revenue),
            "revenue_growth": revenue_growth,
        }
        period_ratios = {"period": inc_periods[i]}
        period_ratios.update({k: v for k, v in candidates.items() if v is not None})
        result.append(period_ratios)
    return result


def _compute_ratios(fin, periods):
    inc_periods, inc = _canonical_ordered(fin.income_statement().to_dataframe())
    _, bal = _canonical_ordered(fin.balance_sheet().to_dataframe())
    _, cf = _canonical_ordered(fin.cash_flow_statement().to_dataframe())
    return _ratios_from_series(inc_periods, inc, bal, cf, periods)


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
        data["ratios"] = _compute_ratios(fin, args.periods)
    payload = output.success(
        "financials",
        {"ticker": args.ticker, "statement": args.statement,
         "periods": args.periods, "ratios": args.ratios, "full": args.full},
        data,
    )
    return payload, "\n\n".join(md_parts)

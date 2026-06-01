from edgar import Company

from .. import output

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


def _statement_records(stmt, periods):
    df = stmt.to_dataframe()
    period_cols = [c for c in df.columns if c not in _METADATA_COLS][:periods]
    rows = []
    for _, row in df.iterrows():
        values = {p: output.sanitize(row[p]) for p in period_cols}
        if all(v is None for v in values.values()):
            continue
        rec = {
            "line_item": output.sanitize(row.get("label")),
            "concept": output.sanitize(row.get("concept")),
        }
        rec.update(values)
        rows.append(rec)
    return rows, period_cols


def run(args):
    c = Company(args.ticker)
    fin = c.get_financials()
    wanted = list(_STATEMENTS) if args.statement == "all" else [args.statement]
    data = {}
    md_parts = []
    for key in wanted:
        stmt = getattr(fin, _STATEMENTS[key])()
        rows, period_cols = _statement_records(stmt, args.periods)
        data[key] = {"periods": period_cols, "rows": rows}
        md_parts.append(f"## {key.title()} statement\n\n{stmt.to_markdown()}")
    if args.ratios:
        primary = "income" if "income" in wanted else wanted[0]
        try:
            data["ratios"] = getattr(fin, _STATEMENTS[primary])().calculate_ratios()
        except Exception as exc:  # ratios are best-effort
            data["ratios"] = {"error": str(exc)}
    payload = output.success(
        "financials",
        {"ticker": args.ticker, "statement": args.statement,
         "periods": args.periods, "ratios": args.ratios},
        data,
    )
    return payload, "\n\n".join(md_parts)

import pandas as pd
from edgar import Company

from .. import output
from ..errors import NoFilingsFound

_COLUMNS = ["Date", "Insider", "Position", "Transaction Type", "Code",
            "Shares", "Price", "Value", "Ticker"]


def _collect(c, limit, since):
    fl = c.get_filings(form="4")
    if fl is None or len(fl) == 0:
        raise NoFilingsFound(f"No Form 4 filings found for {c.name}.")
    frames = []
    skipped = 0
    for i in range(min(limit, len(fl))):
        try:
            frames.append(fl[i].obj().to_dataframe())
        except Exception:
            skipped += 1
            continue
    if not frames:
        raise NoFilingsFound(
            f"No parseable Form 4 transactions for {c.name} "
            f"({skipped} filing(s) failed to parse)."
        )
    combined = pd.concat(frames, ignore_index=True)
    if since and "Date" in combined.columns:
        combined = combined[combined["Date"].astype(str) >= since]
    return combined


def run(args):
    c = Company(args.ticker)
    df = _collect(c, args.limit, args.since)
    if args.net:
        grouped = (
            df.groupby("Transaction Type")
              .agg(count=("Shares", "size"),
                   total_shares=("Shares", "sum"),
                   total_value=("Value", "sum"))
              .reset_index()
        )
        rows = output.dataframe_to_records(grouped)
        data = {"net_by_type": rows}
        md = output.records_to_markdown(rows, title=f"Net insider activity — {args.ticker}")
    else:
        rows = output.dataframe_to_records(df, columns=_COLUMNS)
        data = {"count": len(rows), "transactions": rows}
        md = output.records_to_markdown(rows, title=f"Insider transactions — {args.ticker}")
    payload = output.success(
        "insiders",
        {"ticker": args.ticker, "limit": args.limit, "since": args.since, "net": args.net},
        data,
    )
    return payload, md

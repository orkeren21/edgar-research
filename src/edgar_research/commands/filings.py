from edgar import Company

from .. import output
from ..errors import NoFilingsFound


def run(args):
    c = Company(args.ticker)
    fl = c.get_filings(form=args.form) if args.form else c.get_filings()
    if fl is None or len(fl) == 0:
        raise NoFilingsFound(
            f"No filings found for {args.ticker}"
            + (f" (form {args.form})" if args.form else "")
        )
    n = min(args.limit, len(fl))
    rows = []
    for i in range(n):
        f = fl[i]
        filing_date = output.sanitize(f.filing_date)
        if args.since and filing_date is not None and str(filing_date) < args.since:
            continue
        rows.append({
            "form": f.form,
            "filing_date": filing_date,
            "accession_no": f.accession_no,
            "report_date": output.sanitize(getattr(f, "report_date", None)),
            "primary_document": getattr(f, "primary_document", None),
            "url": getattr(f, "filing_url", None),
        })
    payload = output.success(
        "filings",
        {"ticker": args.ticker, "form": args.form, "limit": args.limit, "since": args.since},
        {"count": len(rows), "filings": rows},
    )
    return payload, output.records_to_markdown(rows, title=f"Filings — {args.ticker}")

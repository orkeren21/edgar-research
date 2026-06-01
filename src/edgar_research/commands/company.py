from edgar import Company

from .. import output


def run(args):
    c = Company(args.ticker)
    data = {
        "name": c.name,
        "cik": c.cik,
        "tickers": list(c.tickers) if getattr(c, "tickers", None) else [],
        "industry": getattr(c, "industry", None),
        "sic": getattr(c, "sic", None),
        "fiscal_year_end": getattr(c, "fiscal_year_end", None),
    }
    recent = c.get_filings().head(5)
    data["recent_filings"] = [
        {
            "form": recent[i].form,
            "filing_date": output.sanitize(recent[i].filing_date),
            "accession_no": recent[i].accession_no,
        }
        for i in range(len(recent))
    ]
    payload = output.success("company", {"ticker": args.ticker}, data)
    card = {k: v for k, v in data.items() if k != "recent_filings"}
    md = output.records_to_markdown([card], title=f"{data['name']} ({data['cik']})")
    return payload, md

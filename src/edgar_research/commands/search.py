from edgar import search_filings

from .. import output

_FIELDS = ["form", "company", "cik", "filed", "accession_number",
           "score", "period", "file_type"]


def run(args):
    kwargs = {}
    if args.forms:
        kwargs["forms"] = args.forms
    if args.date_range:
        kwargs["date"] = args.date_range
    res = search_filings(args.query, **kwargs)
    head = res.head(args.limit)
    items = getattr(head, "results", []) or []
    rows = [{f: output.sanitize(getattr(r, f, None)) for f in _FIELDS} for r in items]
    data = {
        "total": getattr(res, "total", len(rows)),
        "count": len(rows),
        "results": rows,
    }
    payload = output.success(
        "search",
        {"query": args.query, "forms": args.forms,
         "date_range": args.date_range, "limit": args.limit},
        data,
    )
    return payload, output.records_to_markdown(rows, title=f"Search — {args.query!r}")

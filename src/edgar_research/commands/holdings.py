from edgar import Company

from .. import output
from ..errors import NoFilingsFound

_COLUMNS = ["Issuer", "Ticker", "Cusip", "Value", "SharesPrnAmount", "Class", "PutCall"]


def run(args):
    c = Company(args.institution)
    fl = c.get_filings(form="13F-HR")
    if fl is None or len(fl) == 0:
        raise NoFilingsFound(
            f"No 13F-HR filings found for {args.institution} (is this an institutional filer?)."
        )
    obj = fl.latest().obj()
    if not getattr(obj, "has_infotable", False):
        raise NoFilingsFound(f"13F-HR for {args.institution} has no holdings info table.")
    df = obj.infotable
    if "Value" in df.columns:
        df = df.sort_values("Value", ascending=False)
    df = df.head(args.limit)
    rows = output.dataframe_to_records(df, columns=_COLUMNS)
    report_period = output.sanitize(getattr(obj, "report_period", None))
    data = {
        "manager": getattr(obj, "management_company_name", None) or getattr(obj, "manager_name", None),
        "report_period": report_period,
        "count": len(rows),
        "holdings": rows,
    }
    payload = output.success(
        "holdings",
        {"institution": args.institution, "limit": args.limit},
        data,
        meta={"as_of": report_period},
    )
    return payload, output.records_to_markdown(rows, title=f"13F holdings — {data['manager']}")

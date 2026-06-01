from edgar import Company

from .. import output
from ..errors import NoFilingsFound, UsageError

_SECTION_ATTR = {
    "risk-factors": "risk_factors",
    "mda": "management_discussion",
    "business": "business",
}


def _available_sections(obj) -> list[str]:
    """Section names whose text is actually present on this filing object.

    edgartools exposes sections per-filing, so a section valid for one company's
    10-K (e.g. risk-factors) may be absent in another's.
    """
    return [name for name, attr in _SECTION_ATTR.items() if getattr(obj, attr, None)]


def run(args):
    c = Company(args.ticker)
    fl = c.get_filings(form=args.form)
    if fl is None or len(fl) == 0:
        raise NoFilingsFound(f"No {args.form} filings found for {args.ticker}.")
    filing = fl.latest()
    if args.section == "full":
        text = filing.text()
    else:
        obj = filing.obj()
        text = getattr(obj, _SECTION_ATTR[args.section], None)
        if not text:
            available = _available_sections(obj)
            hint = (f" Available sections in this filing: {', '.join(available)}."
                    if available else "")
            raise UsageError(
                f"Section '{args.section}' not available in {args.form} for {args.ticker}."
                f"{hint} Or use --section full."
            )
    text = text or ""
    total = len(text)
    clipped = text[: args.max_chars]
    data = {
        "form": filing.form,
        "section": args.section,
        "accession_no": filing.accession_no,
        "filing_date": output.sanitize(filing.filing_date),
        "length": total,
        "truncated": total > args.max_chars,
        "text": clipped,
    }
    payload = output.success(
        "read",
        {"ticker": args.ticker, "form": args.form,
         "section": args.section, "max_chars": args.max_chars},
        data,
    )
    return payload, clipped

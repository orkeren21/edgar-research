from edgar import Company

from .. import output
from ..errors import NoFilingsFound, UsageError

_SECTION_ATTR = {
    "risk-factors": "risk_factors",
    "mda": "management_discussion",
    "business": "business",
}

_ANNUAL_FORMS = ("10-K", "20-F", "40-F")


def _pick_latest_annual(filings):
    """Most recent filing whose form is an annual report (10-K/20-F/40-F), else None."""
    annual = [f for f in filings if getattr(f, "form", None) in _ANNUAL_FORMS]
    if not annual:
        return None
    return max(annual, key=lambda f: f.filing_date)


def _available_sections(obj) -> list[str]:
    """Section names whose text is actually present on this filing object.

    edgartools exposes sections per-filing, so a section valid for one company's
    10-K (e.g. risk-factors) may be absent in another's.
    """
    return [name for name, attr in _SECTION_ATTR.items() if getattr(obj, attr, None)]


def run(args):
    c = Company(args.ticker)
    if args.form:
        fl = c.get_filings(form=args.form)
        filing = fl.latest() if (fl is not None and len(fl) > 0) else None
        form_label = args.form
    else:
        fl = c.get_filings(form=list(_ANNUAL_FORMS))
        candidates = [fl[i] for i in range(len(fl))] if fl is not None else []
        filing = _pick_latest_annual(candidates)
        form_label = "annual report (10-K/20-F/40-F)"
    if filing is None:
        raise NoFilingsFound(f"No {form_label} filings found for {args.ticker}.")
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
                f"Section '{args.section}' not available in {filing.form} for {args.ticker}."
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

"""edgar-research CLI: argparse dispatch over the command modules."""
from __future__ import annotations

import argparse
import sys

from . import errors, identity, output
from .commands import (
    company, financials, filings, read, insiders, holdings, search,
)

COMMANDS = {
    "company": company,
    "financials": financials,
    "filings": filings,
    "read": read,
    "insiders": insiders,
    "holdings": holdings,
    "search": search,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="edgar-research",
        description="SEC EDGAR research toolkit for investment investigation (edgartools wrapper).",
    )
    p.add_argument("--markdown", action="store_true",
                   help="Human-readable output instead of JSON.")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("company", help="Company identity card.")
    sp.add_argument("ticker", help="Ticker symbol or CIK.")

    sp = sub.add_parser("financials", help="Multi-period financial statements.")
    sp.add_argument("ticker")
    sp.add_argument("--statement", choices=["income", "balance", "cashflow", "all"], default="all")
    sp.add_argument("--periods", type=int, default=4)
    sp.add_argument("--ratios", action="store_true", help="Include derived ratios.")

    sp = sub.add_parser("filings", help="List a company's filings.")
    sp.add_argument("ticker")
    sp.add_argument("--form", default=None, help="Filter by form type, e.g. 10-K.")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--since", default=None, help="Only filings on/after YYYY-MM-DD.")

    sp = sub.add_parser("read", help="Extract readable text from a filing.")
    sp.add_argument("ticker")
    sp.add_argument("--form", default="10-K")
    sp.add_argument("--section", choices=["risk-factors", "mda", "business", "full"], default="full")
    sp.add_argument("--max-chars", type=int, default=50000)

    sp = sub.add_parser("insiders", help="Recent insider (Form 4) transactions.")
    sp.add_argument("ticker")
    sp.add_argument("--limit", type=int, default=10, help="Number of recent Form 4 filings to flatten.")
    sp.add_argument("--since", default=None, help="Only transactions on/after YYYY-MM-DD.")
    sp.add_argument("--net", action="store_true", help="Aggregate buys vs sells instead of listing rows.")

    sp = sub.add_parser("holdings", help="Latest 13F-HR portfolio of an institution.")
    sp.add_argument("institution", help="Ticker or CIK of the institutional filer.")
    sp.add_argument("--limit", type=int, default=50, help="Top N holdings by value.")

    sp = sub.add_parser("search", help="Full-text EDGAR search.")
    sp.add_argument("query")
    sp.add_argument("--form", dest="forms", default=None, help="Restrict to a form type.")
    sp.add_argument("--date-range", dest="date_range", default=None, help="YYYY-MM-DD:YYYY-MM-DD")
    sp.add_argument("--limit", type=int, default=20)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        identity.apply_identity()
        payload, markdown_text = COMMANDS[args.command].run(args)
        print(output.render(payload, markdown=args.markdown, markdown_text=markdown_text))
        return 0
    except Exception as exc:  # top-level boundary: classify everything
        err = errors.classify(exc)
        print(output.render(output.failure(err.error_type, err.message), markdown=args.markdown))
        return err.exit_code


if __name__ == "__main__":
    sys.exit(main())

import datetime as dt

from edgar_research.commands import read


class _F:
    def __init__(self, form, date):
        self.form = form
        self.filing_date = date


def test_pick_latest_annual_picks_most_recent_annual():
    filings = [
        _F("6-K", dt.date(2026, 5, 1)),
        _F("20-F", dt.date(2026, 4, 15)),
        _F("10-K", dt.date(2024, 2, 1)),
        _F("8-K", dt.date(2026, 6, 1)),
    ]
    picked = read._pick_latest_annual(filings)
    assert picked.form == "20-F"
    assert picked.filing_date == dt.date(2026, 4, 15)


def test_pick_latest_annual_none_when_no_annual():
    filings = [_F("6-K", dt.date(2026, 5, 1)), _F("8-K", dt.date(2026, 6, 1))]
    assert read._pick_latest_annual(filings) is None

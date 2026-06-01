import json

import pytest

from edgar_research import cli

pytestmark = pytest.mark.live


def _run(capsys, argv):
    rc = cli.main(argv)
    out = capsys.readouterr().out
    return rc, json.loads(out)


def test_company_live(capsys):
    rc, out = _run(capsys, ["company", "AAPL"])
    assert rc == 0 and out["ok"] is True
    assert "Apple" in out["data"]["name"]
    assert out["data"]["cik"] == 320193


def test_financials_live(capsys):
    rc, out = _run(capsys, ["financials", "AAPL", "--statement", "income", "--periods", "3"])
    assert rc == 0 and out["ok"] is True
    income = out["data"]["income"]
    assert len(income["periods"]) >= 1
    assert len(income["rows"]) > 0
    assert any("revenue" in (r["line_item"] or "").lower()
               or "net sales" in (r["line_item"] or "").lower()
               for r in income["rows"])


def test_filings_live(capsys):
    rc, out = _run(capsys, ["filings", "AAPL", "--form", "10-K", "--limit", "3"])
    assert rc == 0 and out["ok"] is True
    rows = out["data"]["filings"]
    assert len(rows) >= 1
    assert all(r["form"] == "10-K" for r in rows)
    assert rows[0]["url"].startswith("https://www.sec.gov/")

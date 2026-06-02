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
    assert any(r.get("canonical") == "revenue" for r in income["rows"])
    # compact headline view (~15 rows), well below the ~47-row full dimensional dump
    assert len(income["rows"]) < 40


def test_financials_full_live(capsys):
    rc_c, out_c = _run(capsys, ["financials", "AAPL", "--statement", "income", "--periods", "3"])
    rc_f, out_f = _run(capsys, ["financials", "AAPL", "--statement", "income", "--periods", "3", "--full"])
    assert rc_c == 0 and rc_f == 0
    assert len(out_f["data"]["income"]["rows"]) > len(out_c["data"]["income"]["rows"])


def test_financials_ratios_live(capsys):
    rc, out = _run(capsys, ["financials", "AAPL", "--statement", "income",
                            "--ratios", "--periods", "3"])
    assert rc == 0 and out["ok"] is True
    ratios = out["data"]["ratios"]
    assert isinstance(ratios, list) and len(ratios) >= 2
    assert "period" in ratios[0] and "net_margin" in ratios[0]
    assert 0 < ratios[0]["net_margin"] < 1
    assert any("revenue_growth" in r for r in ratios)


def test_filings_live(capsys):
    rc, out = _run(capsys, ["filings", "AAPL", "--form", "10-K", "--limit", "3"])
    assert rc == 0 and out["ok"] is True
    rows = out["data"]["filings"]
    assert len(rows) >= 1
    assert all(r["form"] == "10-K" for r in rows)
    assert rows[0]["url"] and rows[0]["url"].startswith("https://www.sec.gov/")


def test_read_live(capsys):
    rc, out = _run(capsys, ["read", "AAPL", "--section", "risk-factors", "--max-chars", "2000"])
    assert rc == 0 and out["ok"] is True
    data = out["data"]
    assert data["form"] == "10-K"
    assert data["section"] == "risk-factors"
    assert data["length"] > 2000 and data["truncated"] is True
    assert len(data["text"]) == 2000


def test_read_auto_form_foreign_live(capsys):
    rc, out = _run(capsys, ["read", "GRRR", "--section", "full", "--max-chars", "1000"])
    assert rc == 0 and out["ok"] is True
    assert out["data"]["form"] == "20-F"
    assert out["data"]["length"] > 0


def test_insiders_live(capsys):
    rc, out = _run(capsys, ["insiders", "AAPL", "--limit", "3"])
    assert rc == 0 and out["ok"] is True
    assert "transactions" in out["data"]
    assert isinstance(out["data"]["transactions"], list)


def test_insiders_net_live(capsys):
    rc, out = _run(capsys, ["insiders", "AAPL", "--limit", "3", "--net"])
    assert rc == 0 and out["ok"] is True
    assert "net_by_type" in out["data"]


def test_holdings_live(capsys):
    rc, out = _run(capsys, ["holdings", "BRK-A", "--limit", "10"])
    assert rc == 0 and out["ok"] is True
    holdings = out["data"]["holdings"]
    assert len(holdings) >= 1
    assert "Issuer" in holdings[0]
    assert holdings[0]["Value"] is not None


def test_search_live(capsys):
    rc, out = _run(capsys, ["search", "artificial intelligence", "--form", "10-K", "--limit", "5"])
    assert rc == 0 and out["ok"] is True
    assert out["data"]["count"] >= 1
    assert "company" in out["data"]["results"][0]

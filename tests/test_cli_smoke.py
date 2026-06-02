import json

import pytest

from edgar_research import cli, errors, output
from edgar_research.commands import company


def test_build_parser_company():
    args = cli.build_parser().parse_args(["company", "AAPL"])
    assert args.command == "company"
    assert args.ticker == "AAPL"
    assert getattr(args, "markdown", False) is False


def test_build_parser_financials_defaults():
    args = cli.build_parser().parse_args(["financials", "MSFT"])
    assert args.statement == "all"
    assert args.periods == 4
    assert args.ratios is False


def test_help_exits_zero():
    with pytest.raises(SystemExit) as e:
        cli.build_parser().parse_args(["--help"])
    assert e.value.code == 0


def test_main_success(monkeypatch, capsys):
    monkeypatch.setattr(cli.identity, "apply_identity", lambda *a, **k: "x@y.com")
    monkeypatch.setattr(
        company, "run",
        lambda args: (output.success("company", {"ticker": "AAPL"}, {"name": "Apple Inc."}), None),
    )
    rc = cli.main(["company", "AAPL"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["data"]["name"] == "Apple Inc."


def test_main_error_envelope(monkeypatch, capsys):
    monkeypatch.setattr(cli.identity, "apply_identity", lambda *a, **k: "x@y.com")

    def boom(args):
        raise errors.CompanyNotFound("nope")

    monkeypatch.setattr(company, "run", boom)
    rc = cli.main(["company", "ZZZZ"])
    assert rc == 3
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["error"]["type"] == "company_not_found"


def test_build_parser_financials_full_flag():
    args = cli.build_parser().parse_args(["financials", "AAPL", "--full"])
    assert args.full is True
    assert cli.build_parser().parse_args(["financials", "AAPL"]).full is False


def test_markdown_accepted_before_and_after_subcommand():
    p = cli.build_parser()
    assert getattr(p.parse_args(["--markdown", "company", "AAPL"]), "markdown", False) is True
    assert getattr(p.parse_args(["company", "--markdown", "AAPL"]), "markdown", False) is True
    assert getattr(p.parse_args(["company", "AAPL"]), "markdown", False) is False


def test_build_parser_all_subcommands():
    parser = cli.build_parser()
    # every subcommand parses with minimal valid args without raising
    parser.parse_args(["company", "AAPL"])
    parser.parse_args(["financials", "AAPL"])
    parser.parse_args(["filings", "AAPL"])
    parser.parse_args(["read", "AAPL"])
    parser.parse_args(["holdings", "BRK-A"])
    parser.parse_args(["search", "ai"])
    insiders_args = parser.parse_args(["insiders", "AAPL"])
    assert insiders_args.since is None  # regression guard for Fix 1
    assert parser.parse_args(["insiders", "AAPL", "--net"]).net is True

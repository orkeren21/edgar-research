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

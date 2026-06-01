import datetime as dt
import json

import numpy as np
import pandas as pd

from edgar_research import output


def test_sanitize_nan_to_none():
    assert output.sanitize(float("nan")) is None
    assert output.sanitize(np.nan) is None
    assert output.sanitize(pd.NaT) is None


def test_sanitize_dates():
    assert output.sanitize(dt.date(2025, 1, 2)) == "2025-01-02"
    assert output.sanitize(pd.Timestamp("2025-01-02")).startswith("2025-01-02")


def test_sanitize_numpy_scalars():
    r_int = output.sanitize(np.int64(5))
    r_float = output.sanitize(np.float64(1.5))
    assert r_int == 5 and isinstance(r_int, int)
    assert r_float == 1.5 and isinstance(r_float, float)


def test_dataframe_to_records():
    df = pd.DataFrame({"a": [1, np.nan], "d": [pd.Timestamp("2025-01-01"), pd.NaT]})
    recs = output.dataframe_to_records(df)
    assert recs[0]["a"] == 1
    assert recs[1]["a"] is None
    assert recs[0]["d"].startswith("2025-01-01")
    assert recs[1]["d"] is None


def test_dataframe_to_records_columns_and_rename():
    df = pd.DataFrame({"a": [1], "b": [2]})
    recs = output.dataframe_to_records(df, columns=["a"], rename={"a": "alpha"})
    assert recs == [{"alpha": 1}]


def test_success_and_failure_envelopes():
    s = output.success("company", {"ticker": "AAPL"}, {"name": "Apple"})
    assert s["ok"] is True and s["command"] == "company"
    assert s["meta"]["source"] == "SEC EDGAR"
    f = output.failure("company_not_found", "nope")
    assert f["ok"] is False and f["error"]["type"] == "company_not_found"


def test_render_json_and_markdown():
    s = output.success("x", {}, {"n": 1})
    assert json.loads(output.render(s))["ok"] is True
    assert output.render(s, markdown=True, markdown_text="# hi") == "# hi"
    f = output.failure("e", "msg")
    assert "Error (e)" in output.render(f, markdown=True)


def test_records_to_markdown():
    md = output.records_to_markdown([{"a": 1, "b": None}], title="T")
    assert "### T" in md
    assert "| a | b |" in md


def test_sanitize_non_finite():
    import numpy as np
    assert output.sanitize(float("inf")) is None
    assert output.sanitize(float("-inf")) is None
    assert output.sanitize(np.float64("inf")) is None


def test_records_to_markdown_escapes_pipe():
    md = output.records_to_markdown([{"name": "Foo | Bar"}], title="T")
    assert "Foo \\| Bar" in md

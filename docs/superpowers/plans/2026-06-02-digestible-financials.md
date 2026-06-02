# Digestible Financials + Agent Ergonomics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `edgar-research` financials agent-digestible — compact-by-default headline statements (GAAP + IFRS), per-period ratios, canonical labels — plus `read` auto-form-detection and `--markdown` accepted anywhere.

**Architecture:** A canonical concept map (`concepts.py`) and a per-period headline extractor in `financials.py` are the shared backbone for the compact output, the canonical labels, and the multi-period ratios. `read` gains a pure `_pick_latest_annual` helper. `cli.py` adds `--full` and makes `--markdown` position-independent via a shared parent parser.

**Tech Stack:** Python 3.11+, `uv`, `edgartools`, `pandas`, `argparse`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-06-02-digestible-financials-design.md`
**Base:** branch `feat/digestible-financials` off merged `main` (`51a5dfe`).

---

## File Structure

```
src/edgar_research/
  concepts.py                    # NEW: CANONICAL alias map + canonical_for()
  commands/financials.py         # CHANGED: headline extractor, compact default + --full,
                                 #          canonical labels, per-period ratios
  commands/read.py               # CHANGED: _pick_latest_annual + auto-form default
  cli.py                         # CHANGED: --full; --markdown anywhere; read --form default None
tests/
  test_concepts.py               # NEW
  test_financials_headline.py    # NEW
  test_financials_ratios.py      # REPLACED (per-period math)
  test_read_form_select.py       # NEW
  test_cli_smoke.py              # CHANGED (--full, --markdown anywhere)
  test_live.py                   # CHANGED (compact default, --full, per-period ratios, GRRR 20-F)
README.md                        # CHANGED
skills/edgar-research/SKILL.md   # CHANGED
```

**Conventions (already in this repo):** every command returns `(payload, markdown_text)`;
`output.success/failure/render/sanitize/records_to_markdown` are the shared helpers; tests
split into deterministic (no network) and `@pytest.mark.live` (run with `RUN_LIVE=1`).
Run deterministic tests with `uv run pytest -q`. Live tests need `EDGAR_IDENTITY` set.

---

### Task 1: `concepts.py` — canonical concept map

**Files:**
- Create: `src/edgar_research/concepts.py`
- Create: `tests/test_concepts.py`

- [ ] **Step 1: Write the failing test**

`tests/test_concepts.py`:
```python
from edgar_research.concepts import canonical_for


def test_canonical_for_gaap():
    assert canonical_for("us-gaap_NetIncomeLoss") == "net_income"
    assert canonical_for("us-gaap_Assets") == "total_assets"
    assert canonical_for("us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax") == "revenue"


def test_canonical_for_ifrs():
    assert canonical_for("ifrs-full_ProfitLoss") == "net_income"
    assert canonical_for("ifrs-full_Revenue") == "revenue"


def test_canonical_for_unmapped_and_none():
    assert canonical_for("us-gaap_SomethingObscure") is None
    assert canonical_for(None) is None
    assert canonical_for("") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_concepts.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'edgar_research.concepts'`.

- [ ] **Step 3: Write `src/edgar_research/concepts.py`**

```python
"""Canonical mapping of headline XBRL concepts (US-GAAP and IFRS) to common names."""
from __future__ import annotations

# canonical name -> source concepts (us-gaap_* and ifrs-full_*) that mean the same thing.
_CANONICAL_SOURCES: dict[str, tuple[str, ...]] = {
    "revenue": (
        "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax",
        "us-gaap_Revenues",
        "us-gaap_SalesRevenueNet",
        "ifrs-full_Revenue",
    ),
    "cost_of_revenue": (
        "us-gaap_CostOfGoodsAndServicesSold",
        "us-gaap_CostOfRevenue",
        "ifrs-full_CostOfSales",
    ),
    "gross_profit": ("us-gaap_GrossProfit", "ifrs-full_GrossProfit"),
    "operating_income": (
        "us-gaap_OperatingIncomeLoss",
        "ifrs-full_ProfitLossFromOperatingActivities",
    ),
    "operating_expenses": ("us-gaap_OperatingExpenses", "ifrs-full_OperatingExpense"),
    "research_and_development": (
        "us-gaap_ResearchAndDevelopmentExpense",
        "ifrs-full_ResearchAndDevelopmentExpense",
    ),
    "net_income": ("us-gaap_NetIncomeLoss", "us-gaap_ProfitLoss", "ifrs-full_ProfitLoss"),
    "total_assets": ("us-gaap_Assets", "ifrs-full_Assets"),
    "total_liabilities": ("us-gaap_Liabilities", "ifrs-full_Liabilities"),
    "stockholders_equity": (
        "us-gaap_StockholdersEquity",
        "us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "ifrs-full_Equity",
    ),
    "current_assets": ("us-gaap_AssetsCurrent", "ifrs-full_CurrentAssets"),
    "current_liabilities": ("us-gaap_LiabilitiesCurrent", "ifrs-full_CurrentLiabilities"),
    "operating_cash_flow": (
        "us-gaap_NetCashProvidedByUsedInOperatingActivities",
        "us-gaap_NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "ifrs-full_CashFlowsFromUsedInOperatingActivities",
    ),
    "capital_expenditures": (
        "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
        "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
    ),
    "eps_basic": ("us-gaap_EarningsPerShareBasic", "ifrs-full_BasicEarningsLossPerShare"),
    "eps_diluted": ("us-gaap_EarningsPerShareDiluted", "ifrs-full_DilutedEarningsLossPerShare"),
}

# Inverted: concept -> canonical name.
_CONCEPT_TO_CANONICAL: dict[str, str] = {
    concept: name
    for name, concepts in _CANONICAL_SOURCES.items()
    for concept in concepts
}


def canonical_for(concept: str | None) -> str | None:
    """Canonical name for an XBRL concept, or None if unmapped/empty."""
    if not concept:
        return None
    return _CONCEPT_TO_CANONICAL.get(concept)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_concepts.py -q`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/edgar_research/concepts.py tests/test_concepts.py
git commit -m "feat: canonical GAAP/IFRS concept map"
```

---

### Task 2: financials — compact-by-default headline output + `--full` + canonical labels

**Files:**
- Modify: `src/edgar_research/commands/financials.py`
- Modify: `src/edgar_research/cli.py`
- Create: `tests/test_financials_headline.py`
- Modify: `tests/test_live.py`
- Modify: `tests/test_cli_smoke.py`

> This task leaves the existing latest-period ratio code untouched (Task 3 replaces it). It
> changes the statement rows to compact-headline-by-default, renames the row key
> `line_item` → `label`, adds a `canonical` field, and adds `--full`.

- [ ] **Step 1: Write the failing test**

`tests/test_financials_headline.py`:
```python
import pandas as pd

from edgar_research.commands import financials as fin


class _Stmt:
    def __init__(self, df):
        self._df = df

    def to_dataframe(self):
        return self._df


def test_is_headline_excludes_abstract_and_dimensional():
    base = {"abstract": False, "dimension": False, "is_breakdown": False}
    assert fin._is_headline(pd.Series(base)) is True
    assert fin._is_headline(pd.Series({**base, "abstract": True})) is False
    assert fin._is_headline(pd.Series({**base, "dimension": True})) is False
    assert fin._is_headline(pd.Series({**base, "is_breakdown": True})) is False


def test_statement_records_compact_drops_noise_and_annotates_canonical():
    df = pd.DataFrame([
        {"concept": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
         "label": "Net sales", "abstract": False, "dimension": False, "is_breakdown": False,
         "2025 (FY)": 100.0, "2024 (FY)": 90.0},
        {"concept": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
         "label": "Americas", "abstract": False, "dimension": True, "is_breakdown": True,
         "2025 (FY)": 40.0, "2024 (FY)": 35.0},          # dimensional -> dropped
        {"concept": "us-gaap_StatementHeader", "label": "Revenue:",
         "abstract": True, "dimension": False, "is_breakdown": False,
         "2025 (FY)": None, "2024 (FY)": None},          # abstract/all-null -> dropped
    ])
    rows, period_cols = fin._statement_records(_Stmt(df), periods=2, full=False)
    assert period_cols == ["2025 (FY)", "2024 (FY)"]
    assert len(rows) == 1
    assert rows[0]["label"] == "Net sales"
    assert rows[0]["concept"] == "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax"
    assert rows[0]["canonical"] == "revenue"
    assert rows[0]["2025 (FY)"] == 100.0


def test_statement_records_full_keeps_dimensional_rows():
    df = pd.DataFrame([
        {"concept": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
         "label": "Net sales", "abstract": False, "dimension": False, "is_breakdown": False,
         "2025 (FY)": 100.0},
        {"concept": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
         "label": "Americas", "abstract": False, "dimension": True, "is_breakdown": True,
         "2025 (FY)": 40.0},
    ])
    rows, _ = fin._statement_records(_Stmt(df), periods=1, full=True)
    assert len(rows) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_financials_headline.py -q`
Expected: FAIL — `_is_headline` doesn't exist and `_statement_records` has no `full` param.

- [ ] **Step 3: Update `financials.py` imports**

Change (top of file):
```python
from .. import output
```
to:
```python
from .. import output
from ..concepts import canonical_for
```

- [ ] **Step 4: Replace `_statement_records` with the headline-aware version**

Replace this entire block:
```python
def _statement_records(stmt, periods):
    df = stmt.to_dataframe()
    period_cols = [c for c in df.columns if c not in _METADATA_COLS][:periods]
    rows = []
    for _, row in df.iterrows():
        values = {p: output.sanitize(row[p]) for p in period_cols}
        if all(v is None for v in values.values()):
            continue
        rec = {
            "line_item": output.sanitize(row.get("label")),
            "concept": output.sanitize(row.get("concept")),
        }
        rec.update(values)
        rows.append(rec)
    return rows, period_cols
```
with:
```python
def _period_columns(df):
    return [c for c in df.columns if c not in _METADATA_COLS]


def _is_headline(row) -> bool:
    """True for a real line item (not an abstract header or dimensional breakdown)."""
    for col in ("abstract", "dimension", "is_breakdown"):
        if col in row and bool(row[col]):
            return False
    return True


def _statement_records(stmt, periods, full=False):
    df = stmt.to_dataframe()
    period_cols = _period_columns(df)[:periods]
    rows = []
    for _, row in df.iterrows():
        if not full and not _is_headline(row):
            continue
        values = {p: output.sanitize(row[p]) for p in period_cols}
        if all(v is None for v in values.values()):
            continue
        rec = {
            "label": output.sanitize(row.get("label")),
            "concept": output.sanitize(row.get("concept")),
            "canonical": canonical_for(row.get("concept")),
        }
        rec.update(values)
        rows.append(rec)
    return rows, period_cols


def _statement_markdown(stmt, rows, full):
    return stmt.to_markdown() if full else output.records_to_markdown(rows)
```

- [ ] **Step 5: Update `run()` for `--full`, the markdown helper, and the `full` query echo**

In `run()`, change:
```python
        rows, period_cols = _statement_records(stmt, args.periods)
        data[key] = {"periods": period_cols, "rows": rows}
        md_parts.append(f"## {key.title()} statement\n\n{stmt.to_markdown()}")
```
to:
```python
        rows, period_cols = _statement_records(stmt, args.periods, full=args.full)
        data[key] = {"periods": period_cols, "rows": rows}
        md_parts.append(f"## {key.title()} statement\n\n" + _statement_markdown(stmt, rows, args.full))
```
And change the `output.success(... )` query dict from:
```python
        {"ticker": args.ticker, "statement": args.statement,
         "periods": args.periods, "ratios": args.ratios},
```
to:
```python
        {"ticker": args.ticker, "statement": args.statement,
         "periods": args.periods, "ratios": args.ratios, "full": args.full},
```

- [ ] **Step 6: Add `--full` to the financials subparser in `cli.py`**

In `cli.py`, in the `financials` subparser block, after the `--ratios` line add:
```python
    sp.add_argument("--full", action="store_true",
                    help="Return the complete statement dump (all dimensional rows) "
                         "instead of the compact headline view.")
```

- [ ] **Step 7: Run the new deterministic test**

Run: `uv run pytest tests/test_financials_headline.py -q`
Expected: PASS (3 tests).

- [ ] **Step 8: Update the live financials tests in `tests/test_live.py`**

Replace `test_financials_live` with:
```python
def test_financials_live(capsys):
    rc, out = _run(capsys, ["financials", "AAPL", "--statement", "income", "--periods", "3"])
    assert rc == 0 and out["ok"] is True
    income = out["data"]["income"]
    assert len(income["periods"]) >= 1
    assert len(income["rows"]) > 0
    assert any(r.get("canonical") == "revenue" for r in income["rows"])
    assert len(income["rows"]) < 25  # compact headline view, not the full dimensional dump


def test_financials_full_live(capsys):
    rc_c, out_c = _run(capsys, ["financials", "AAPL", "--statement", "income", "--periods", "3"])
    rc_f, out_f = _run(capsys, ["financials", "AAPL", "--statement", "income", "--periods", "3", "--full"])
    assert rc_c == 0 and rc_f == 0
    assert len(out_f["data"]["income"]["rows"]) > len(out_c["data"]["income"]["rows"])
```

- [ ] **Step 9: Add a `--full` smoke test in `tests/test_cli_smoke.py`**

Add:
```python
def test_build_parser_financials_full_flag():
    args = cli.build_parser().parse_args(["financials", "AAPL", "--full"])
    assert args.full is True
    assert cli.build_parser().parse_args(["financials", "AAPL"]).full is False
```

- [ ] **Step 10: Run the deterministic suite**

Run: `uv run pytest -q`
Expected: PASS; live tests skipped. (If `test_financials_ratios_live` references `data["ratios"]` as a dict it still passes — ratios are unchanged in this task.)

- [ ] **Step 11: Verify live**

Run: `RUN_LIVE=1 uv run pytest tests/test_live.py::test_financials_live tests/test_live.py::test_financials_full_live -q`
Expected: PASS.

- [ ] **Step 12: Commit**

```bash
git add src/edgar_research/commands/financials.py src/edgar_research/cli.py \
        tests/test_financials_headline.py tests/test_live.py tests/test_cli_smoke.py
git commit -m "feat: compact-by-default headline financials + --full + canonical labels"
```

---

### Task 3: financials — multi-period ratios

**Files:**
- Modify: `src/edgar_research/commands/financials.py`
- Replace: `tests/test_financials_ratios.py`
- Modify: `tests/test_live.py`

> Replaces the latest-only `get_financial_metrics()` ratio path with per-period ratios
> computed from canonical statement values. `data.ratios` becomes a newest-first list.

- [ ] **Step 1: Replace `tests/test_financials_ratios.py` (write the new failing tests)**

Overwrite the file with:
```python
from edgar_research.commands import financials as fin


def test_safe_div():
    assert fin._safe_div(10, 2) == 5
    assert fin._safe_div(10, 0) is None
    assert fin._safe_div(None, 2) is None
    assert fin._safe_div(10, None) is None


def test_val_indexing():
    assert fin._val({"revenue": [1.0, 2.0]}, "revenue", 0) == 1.0
    assert fin._val({"revenue": [1.0]}, "revenue", 5) is None
    assert fin._val({}, "revenue", 0) is None


def test_ratios_from_series_per_period_identity_and_growth():
    periods = ["2025 (FY)", "2024 (FY)"]
    inc = {
        "revenue": [1000.0, 800.0],
        "net_income": [200.0, 120.0],
        "operating_income": [300.0, 200.0],
        "gross_profit": [500.0, 400.0],
    }
    bal = {
        "total_assets": [4000.0, 3500.0],
        "stockholders_equity": [1500.0, 1400.0],
        "current_assets": [800.0, 700.0],
        "current_liabilities": [400.0, 350.0],
    }
    cf = {"operating_cash_flow": [350.0, 250.0], "capital_expenditures": [50.0, 40.0]}

    out = fin._ratios_from_series(periods, inc, bal, cf, periods=2)
    assert [r["period"] for r in out] == periods
    p0 = out[0]
    assert p0["gross_margin"] == 0.5
    assert p0["operating_margin"] == 0.3
    assert p0["net_margin"] == 0.2
    assert p0["debt_to_assets"] == (4000.0 - 1500.0) / 4000.0   # identity, not tagged liabilities
    assert p0["debt_to_equity"] == (4000.0 - 1500.0) / 1500.0
    assert p0["current_ratio"] == 2.0
    assert p0["fcf_margin"] == (350.0 - 50.0) / 1000.0
    assert p0["revenue_growth"] == (1000.0 - 800.0) / 800.0
    assert "revenue_growth" not in out[1]            # oldest period has no prior


def test_ratios_from_series_omits_missing_inputs():
    out = fin._ratios_from_series(["2025 (FY)"], {"net_income": [100.0]}, {}, {}, periods=1)
    assert out == [{"period": "2025 (FY)"}]
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_financials_ratios.py -q`
Expected: FAIL — `_val` and `_ratios_from_series` don't exist yet.

- [ ] **Step 3: Replace the ratio code in `financials.py`**

Delete these now-obsolete blocks: `_REVENUE_CONCEPTS`, `_ratios_from_metrics`, `_latest_two_revenue`, and the old `_compute_ratios`. Keep `_safe_div`. Then add the new ratio engine (place it after `_statement_markdown`, keeping `_safe_div` where it is or move it adjacent):

```python
def _canonical_ordered(df):
    """(period_labels, {canonical_name: [values aligned to period_labels]}).

    Reads only headline rows; the first match per canonical name wins (the headline
    line, not a dimensional duplicate sharing the same concept).
    """
    if "concept" not in df.columns:
        return [], {}
    period_cols = _period_columns(df)
    series = {}
    for _, row in df.iterrows():
        if not _is_headline(row):
            continue
        name = canonical_for(row.get("concept"))
        if name is None or name in series:
            continue
        series[name] = [output.sanitize(row[p]) for p in period_cols]
    return period_cols, series


def _val(series, name, i):
    vals = series.get(name)
    if vals is None or i >= len(vals):
        return None
    return vals[i]


def _ratios_from_series(inc_periods, inc, bal, cf, periods):
    """Pure per-period ratios from ordered canonical series (newest-first)."""
    n = min(len(inc_periods), periods) if inc_periods else 0
    result = []
    for i in range(n):
        revenue = _val(inc, "revenue", i)
        net_income = _val(inc, "net_income", i)
        operating_income = _val(inc, "operating_income", i)
        gross_profit = _val(inc, "gross_profit", i)
        total_assets = _val(bal, "total_assets", i)
        equity = _val(bal, "stockholders_equity", i)
        current_assets = _val(bal, "current_assets", i)
        current_liabilities = _val(bal, "current_liabilities", i)
        ocf = _val(cf, "operating_cash_flow", i)
        capex = _val(cf, "capital_expenditures", i)
        # Liabilities via the accounting identity (Assets - Equity); edgartools' tagged
        # total_liabilities can mis-map to LiabilitiesAndStockholdersEquity (== assets).
        liabilities = (total_assets - equity) if (total_assets is not None and equity is not None) else None
        fcf = (ocf - capex) if (ocf is not None and capex is not None) else None
        prior_revenue = _val(inc, "revenue", i + 1)
        revenue_growth = (
            (revenue - prior_revenue) / prior_revenue
            if (revenue is not None and prior_revenue not in (None, 0)) else None
        )
        candidates = {
            "gross_margin": _safe_div(gross_profit, revenue),
            "operating_margin": _safe_div(operating_income, revenue),
            "net_margin": _safe_div(net_income, revenue),
            "return_on_equity": _safe_div(net_income, equity),
            "return_on_assets": _safe_div(net_income, total_assets),
            "current_ratio": _safe_div(current_assets, current_liabilities),
            "debt_to_equity": _safe_div(liabilities, equity),
            "debt_to_assets": _safe_div(liabilities, total_assets),
            "fcf_margin": _safe_div(fcf, revenue),
            "revenue_growth": revenue_growth,
        }
        period_ratios = {"period": inc_periods[i]}
        period_ratios.update({k: v for k, v in candidates.items() if v is not None})
        result.append(period_ratios)
    return result


def _compute_ratios(fin, periods):
    inc_periods, inc = _canonical_ordered(fin.income_statement().to_dataframe())
    _, bal = _canonical_ordered(fin.balance_sheet().to_dataframe())
    _, cf = _canonical_ordered(fin.cash_flow_statement().to_dataframe())
    return _ratios_from_series(inc_periods, inc, bal, cf, periods)
```

- [ ] **Step 4: Update the `run()` ratios call**

Change:
```python
    if args.ratios:
        data["ratios"] = _compute_ratios(fin)
```
to:
```python
    if args.ratios:
        data["ratios"] = _compute_ratios(fin, args.periods)
```

- [ ] **Step 5: Run the new deterministic ratio test**

Run: `uv run pytest tests/test_financials_ratios.py -q`
Expected: PASS (4 tests).

- [ ] **Step 6: Update the live ratios test in `tests/test_live.py`**

Replace `test_financials_ratios_live` with:
```python
def test_financials_ratios_live(capsys):
    rc, out = _run(capsys, ["financials", "AAPL", "--statement", "income",
                            "--ratios", "--periods", "3"])
    assert rc == 0 and out["ok"] is True
    ratios = out["data"]["ratios"]
    assert isinstance(ratios, list) and len(ratios) >= 2
    assert "period" in ratios[0] and "net_margin" in ratios[0]
    assert 0 < ratios[0]["net_margin"] < 1
    assert any("revenue_growth" in r for r in ratios)
```

- [ ] **Step 7: Run the full deterministic suite**

Run: `uv run pytest -q`
Expected: PASS; live skipped.

- [ ] **Step 8: Verify live**

Run: `RUN_LIVE=1 uv run pytest tests/test_live.py::test_financials_ratios_live -q`
Expected: PASS (per-period list with `net_margin` and at least one `revenue_growth`).

- [ ] **Step 9: Commit**

```bash
git add src/edgar_research/commands/financials.py tests/test_financials_ratios.py tests/test_live.py
git commit -m "feat: multi-period ratios (per-period list from canonical statement values)"
```

---

### Task 4: `read` — auto-detect the annual report

**Files:**
- Modify: `src/edgar_research/commands/read.py`
- Modify: `src/edgar_research/cli.py`
- Create: `tests/test_read_form_select.py`
- Modify: `tests/test_live.py`

- [ ] **Step 1: Write the failing test**

`tests/test_read_form_select.py`:
```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_read_form_select.py -q`
Expected: FAIL — `_pick_latest_annual` doesn't exist.

- [ ] **Step 3: Add the helper + annual-forms constant in `read.py`**

After the `_SECTION_ATTR` dict, add:
```python
_ANNUAL_FORMS = ("10-K", "20-F", "40-F")


def _pick_latest_annual(filings):
    """Most recent filing whose form is an annual report (10-K/20-F/40-F), else None."""
    annual = [f for f in filings if getattr(f, "form", None) in _ANNUAL_FORMS]
    if not annual:
        return None
    return max(annual, key=lambda f: f.filing_date)
```

- [ ] **Step 4: Update `run()` to default to the latest annual report**

Replace this block at the top of `run()`:
```python
    c = Company(args.ticker)
    fl = c.get_filings(form=args.form)
    if fl is None or len(fl) == 0:
        raise NoFilingsFound(f"No {args.form} filings found for {args.ticker}.")
    filing = fl.latest()
```
with:
```python
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
```
And in the `UsageError` message, change `in {args.form} for` to `in {filing.form} for`:
```python
            raise UsageError(
                f"Section '{args.section}' not available in {filing.form} for {args.ticker}."
                f"{hint} Or use --section full."
            )
```

- [ ] **Step 5: Change the `read --form` default to `None` in `cli.py`**

In `cli.py`, in the `read` subparser, change:
```python
    sp.add_argument("--form", default="10-K")
```
to:
```python
    sp.add_argument("--form", default=None,
                    help="Form type (e.g. 10-K, 20-F). Default: latest annual report "
                         "(10-K/20-F/40-F).")
```

- [ ] **Step 6: Run the new deterministic test**

Run: `uv run pytest tests/test_read_form_select.py -q`
Expected: PASS (2 tests).

- [ ] **Step 7: Update the live `read` tests in `tests/test_live.py`**

Replace `test_read_live` with (drop the explicit `--form 10-K`; auto-form must resolve to the 10-K for AAPL), and add a foreign-issuer test:
```python
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
```

- [ ] **Step 8: Run the deterministic suite**

Run: `uv run pytest -q`
Expected: PASS; live skipped.

- [ ] **Step 9: Verify live**

Run: `RUN_LIVE=1 uv run pytest tests/test_live.py::test_read_live tests/test_live.py::test_read_auto_form_foreign_live -q`
Expected: PASS (AAPL auto-resolves 10-K; GRRR auto-resolves 20-F).

- [ ] **Step 10: Commit**

```bash
git add src/edgar_research/commands/read.py src/edgar_research/cli.py \
        tests/test_read_form_select.py tests/test_live.py
git commit -m "feat: read auto-detects the latest annual report (10-K/20-F/40-F)"
```

---

### Task 5: `--markdown` accepted before OR after the subcommand

**Files:**
- Modify: `src/edgar_research/cli.py`
- Modify: `tests/test_cli_smoke.py`

> Uses a shared parent parser whose `--markdown` has `default=argparse.SUPPRESS`, added to
> both the top parser and every subparser. SUPPRESS means the `markdown` attribute is set
> only when the flag is actually given (at either position), so neither parse clobbers the
> other. `main()` reads it with `getattr(args, "markdown", False)`.

- [ ] **Step 1: Update the smoke tests (write the failing expectation)**

In `tests/test_cli_smoke.py`, change the existing assertion in `test_build_parser_company`
from:
```python
    assert args.markdown is False
```
to:
```python
    assert getattr(args, "markdown", False) is False
```
And add a new test:
```python
def test_markdown_accepted_before_and_after_subcommand():
    p = cli.build_parser()
    assert getattr(p.parse_args(["--markdown", "company", "AAPL"]), "markdown", False) is True
    assert getattr(p.parse_args(["company", "--markdown", "AAPL"]), "markdown", False) is True
    assert getattr(p.parse_args(["company", "AAPL"]), "markdown", False) is False
```

- [ ] **Step 2: Run to verify the new test fails**

Run: `uv run pytest tests/test_cli_smoke.py::test_markdown_accepted_before_and_after_subcommand -q`
Expected: FAIL — `--markdown` after the subcommand is currently rejected/unrecognized.

- [ ] **Step 3: Restructure `build_parser()` to share a markdown parent parser**

Replace the top of `build_parser()`:
```python
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="edgar-research",
        description="SEC EDGAR research toolkit for investment investigation (edgartools wrapper).",
    )
    p.add_argument("--markdown", action="store_true",
                   help="Human-readable output instead of JSON.")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("company", help="Company identity card.")
```
with:
```python
def build_parser() -> argparse.ArgumentParser:
    md_parent = argparse.ArgumentParser(add_help=False)
    md_parent.add_argument(
        "--markdown", action="store_true", default=argparse.SUPPRESS,
        help="Human-readable output instead of JSON (accepted before or after the subcommand).",
    )
    p = argparse.ArgumentParser(
        prog="edgar-research",
        parents=[md_parent],
        description="SEC EDGAR research toolkit for investment investigation (edgartools wrapper).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("company", parents=[md_parent], help="Company identity card.")
```
Then add `parents=[md_parent]` to **every** remaining `sub.add_parser(...)` call
(`financials`, `filings`, `read`, `insiders`, `holdings`, `search`), e.g.:
```python
    sp = sub.add_parser("financials", parents=[md_parent], help="Multi-period financial statements.")
    ...
    sp = sub.add_parser("filings", parents=[md_parent], help="List a company's filings.")
    ...
    sp = sub.add_parser("read", parents=[md_parent], help="Extract readable text from a filing.")
    ...
    sp = sub.add_parser("insiders", parents=[md_parent], help="Recent insider (Form 4) transactions.")
    ...
    sp = sub.add_parser("holdings", parents=[md_parent], help="Latest 13F-HR portfolio of an institution.")
    ...
    sp = sub.add_parser("search", parents=[md_parent], help="Full-text EDGAR search.")
```

- [ ] **Step 4: Update `main()` to read markdown via `getattr`**

In `main()`, change:
```python
        payload, markdown_text = COMMANDS[args.command].run(args)
        print(output.render(payload, markdown=args.markdown, markdown_text=markdown_text))
        return 0
    except Exception as exc:  # top-level boundary: classify everything
        err = errors.classify(exc)
        print(output.render(output.failure(err.error_type, err.message), markdown=args.markdown))
        return err.exit_code
```
to:
```python
        markdown = getattr(args, "markdown", False)
        payload, markdown_text = COMMANDS[args.command].run(args)
        print(output.render(payload, markdown=markdown, markdown_text=markdown_text))
        return 0
    except Exception as exc:  # top-level boundary: classify everything
        markdown = getattr(args, "markdown", False)
        err = errors.classify(exc)
        print(output.render(output.failure(err.error_type, err.message), markdown=markdown))
        return err.exit_code
```

- [ ] **Step 5: Run the smoke tests**

Run: `uv run pytest tests/test_cli_smoke.py -q`
Expected: PASS (all, including the new before/after test).

- [ ] **Step 6: Verify the real CLI accepts both positions**

Run:
```bash
EDGAR_IDENTITY=test@example.com uv run edgar-research company AAPL --markdown >/dev/null && echo "after-OK"
EDGAR_IDENTITY=test@example.com uv run edgar-research --markdown company AAPL >/dev/null && echo "before-OK"
```
Expected: both print their `OK` line (exit 0).

- [ ] **Step 7: Commit**

```bash
git add src/edgar_research/cli.py tests/test_cli_smoke.py
git commit -m "feat: accept --markdown before or after the subcommand"
```

---

### Task 6: Docs — SKILL.md + README

**Files:**
- Modify: `skills/edgar-research/SKILL.md`
- Modify: `README.md`

- [ ] **Step 1: Update `skills/edgar-research/SKILL.md`**

(a) In the **Setup** section, after the Invocation bullet, add a note (it follows the existing
`uvx --from …` line):
```markdown
- **First call is slow:** the first `uvx --from git+… edgar-research …` run takes ~15–20s to
  fetch and build dependencies; subsequent calls are cached and fast.
```

(b) Replace the **Commands** table rows for `financials` and `read` with:
```markdown
| `financials TICKER [--statement income\|balance\|cashflow\|all] [--periods N] [--ratios] [--full]` | Compact headline statements by default (dimensional/zero rows dropped, `canonical` label added); `--ratios` adds per-period ratios; `--full` returns the complete dump |
| `read TICKER [--form 10-K] [--section risk-factors\|mda\|business\|full] [--max-chars N]` | Read filing prose. With no `--form`, defaults to the latest annual report (10-K/20-F/40-F — handles foreign issuers) |
```

(c) Replace recommended-sequence steps 2 and 3 with:
```markdown
2. `financials TICKER --statement all --periods 5 --ratios` — compact headline lines by
   default, each tagged with a `canonical` name; `--ratios` returns a per-period list
   (margins, ROE/ROA, leverage, revenue growth). Add `--full` only if you need the complete
   dimensional dump.
3. `read TICKER --section risk-factors`, then `--section mda` — no `--form` needed; it finds
   the latest annual report (10-K or, for foreign issuers, 20-F). If a section is unavailable
   the error lists which ones are; or use `--section full`.
```

(d) Replace the gotchas rows for `--ratios` and `--periods` with:
```markdown
| Financials output | Compact headline lines by default; pass `--full` for every dimensional/segment row. Each row has a `canonical` field (null when unmapped). |
| `--ratios` shape | A **per-period list** under `data.ratios`, newest-first, each `{period, …ratios}`; a ratio is omitted for a period when its inputs are missing. |
| `--periods N` returns fewer than N | `N` is "up to N most recent" — bounded by available XBRL periods. |
```

- [ ] **Step 2: Update `README.md`**

(a) In the **Commands** table, replace the `financials` and `read` rows with:
```markdown
| `financials TICKER [--statement income\|balance\|cashflow\|all] [--periods N] [--ratios] [--full]` | Compact headline statements (`--full` for the complete dump) + optional per-period ratios |
| `read TICKER [--form 10-K] [--section risk-factors\|mda\|business\|full] [--max-chars N]` | Read filing prose; defaults to the latest annual report (10-K/20-F/40-F) when `--form` is omitted |
```

(b) In **Notes & limitations**, replace the `financials`/`--ratios` bullet with:
```markdown
- `financials` returns **compact headline lines by default** (dimensional/segment/zero rows
  dropped; each row carries a `canonical` label where recognized). Pass `--full` for the
  complete dump. `--ratios` returns a **per-period list** in `data.ratios` (gross/operating/net
  margin, ROE, ROA, current ratio, debt-to-equity, debt-to-assets, FCF margin, revenue growth),
  omitting any ratio whose inputs are missing for that period.
- `read` defaults to the latest annual report across 10-K / 20-F / 40-F when `--form` is
  omitted (so foreign private issuers work without specifying the form).
```

(c) Under **Output contract**, after the `--markdown` sentence, add:
```markdown
`--markdown` may be placed before or after the subcommand.
```

- [ ] **Step 3: Sanity-check the docs render**

Run: `uv run python -c "import pathlib; print('SKILL ok', len(pathlib.Path('skills/edgar-research/SKILL.md').read_text())); print('README ok', len(pathlib.Path('README.md').read_text()))"`
Expected: prints both lengths (files readable).

- [ ] **Step 4: Commit**

```bash
git add skills/edgar-research/SKILL.md README.md
git commit -m "docs: compact financials, per-period ratios, read auto-form, markdown anywhere"
```

---

### Task 7: Full verification pass

**Files:** none (verification only)

- [ ] **Step 1: Deterministic suite**

Run: `uv run pytest -q`
Expected: all unit/smoke tests PASS; all `test_live.py` tests SKIPPED.

- [ ] **Step 2: Full live suite**

Run: `EDGAR_IDENTITY=you@example.com RUN_LIVE=1 uv run pytest -q`
Expected: every test PASSES (including the new compact/full, per-period ratios, and GRRR 20-F live tests).

- [ ] **Step 3: Manual eyeball — compact default vs full, GAAP + IFRS**

```bash
export EDGAR_IDENTITY=you@example.com
uv run edgar-research financials AAPL --statement income | python3 -c "import sys,json;d=json.load(sys.stdin);print('AAPL compact rows:',len(d['data']['income']['rows']))"
uv run edgar-research financials AAPL --statement income --full | python3 -c "import sys,json;d=json.load(sys.stdin);print('AAPL full rows:',len(d['data']['income']['rows']))"
uv run edgar-research financials GRRR --statement income | python3 -c "import sys,json;d=json.load(sys.stdin);print('GRRR compact rows:',len(d['data']['income']['rows']),'| canonical present:',any(r['canonical'] for r in d['data']['income']['rows']))"
uv run edgar-research financials AAPL --statement all --ratios | python3 -c "import sys,json;d=json.load(sys.stdin);print('ratios periods:',[r['period'] for r in d['data']['ratios']])"
uv run edgar-research read GRRR --section full --max-chars 200 | python3 -c "import sys,json;print('read GRRR form:',json.load(sys.stdin)['data']['form'])"
```
Expected: compact rows ≪ full rows; GRRR shows canonical labels; ratios lists multiple periods; `read GRRR` → form `20-F`.

- [ ] **Step 4: Final commit (allow empty)**

```bash
git add -A && git commit -m "chore: verification pass" --allow-empty
```

---

## Self-Review

**Spec coverage:**
- Backbone (per-period canonical extraction) → `concepts.py` (Task 1) + `_canonical_ordered`/`_is_headline` (Tasks 2–3). ✓
- Compact-by-default financials + `--full` → Task 2. ✓
- Canonical labels on rows (#5) → `canonical` field, Task 2; canonical map, Task 1. ✓
- Multi-period ratios as a per-period list (#2) → Task 3. ✓
- `read` auto-form-detection (#3) → Task 4. ✓
- `--markdown` anywhere (#6) → Task 5. ✓
- uvx timing note + docs → Task 6. ✓
- Tests: concepts lookup, headline filtering, per-period ratio math + identity + growth + omission, `_pick_latest_annual`, CLI smoke (`--full`, markdown-anywhere), live (AAPL+GRRR compact/full, per-period ratios, GRRR 20-F) → Tasks 1–4. ✓
- Out of scope (jq `--fields`, broad normalization) → not present. ✓

**Placeholder scan:** No TBD/TODO; every code step shows complete code; every test step shows assertions and expected pass/fail.

**Type consistency:** `_statement_records(stmt, periods, full=False)`, `_is_headline(row)`,
`_canonical_ordered(df) -> (list, dict)`, `_val(series, name, i)`,
`_ratios_from_series(inc_periods, inc, bal, cf, periods) -> list`, `_compute_ratios(fin, periods)`,
`canonical_for(concept) -> str|None`, `_pick_latest_annual(filings)` — names/signatures are used
consistently across tasks and tests. Row key is `label` (not `line_item`) everywhere from Task 2 on.
`data.ratios` is a list from Task 3 on, and the live test is updated in the same task. `--markdown`
read via `getattr(args, "markdown", False)` everywhere it's consumed (Task 5).

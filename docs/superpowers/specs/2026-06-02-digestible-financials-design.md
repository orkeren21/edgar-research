# Design: edgar-research v2 — digestible financials + agent ergonomics

**Date:** 2026-06-02
**Status:** Approved (design phase)
**Builds on:** PR #3 (`feat/real-ratios`, merged) — replaces its latest-only ratio path.

## Motivation

Feedback from real Cowork agent runs (notably an IFRS / 20-F foreign issuer, GRRR):

1. **Verbose financials are the #1 problem.** `financials --statement all` dumps every
   segment / geography / XBRL dimensional "member" row flat, including dozens of zero/null
   rows. Agents nearly burn context and resort to writing a flattening snippet. Output
   size = tokens, so this matters doubly inside LLM agents.
2. `--ratios` only attaches **latest-period** values; multi-year margin trends (the actual
   story for several filers) must be recomputed by hand.
3. `read` leans on `10-K`; foreign private issuers file `20-F` (or `40-F`), so the agent
   had to *know* to pass `--form 20-F`.
4. Labels differ across GAAP/IFRS (`us-gaap_NetIncomeLoss` "Net income" vs
   `ifrs-full_ProfitLoss` "Profit (loss)"), hurting cross-company comparison.
5. `--markdown` must precede the subcommand — easy to fumble.

What the feedback explicitly validated as **good and not to change**: the `{ok, data, meta}`
envelope, the error contract + exit codes, and the SKILL.md gotchas table (the 13F
"filer-centric" and "`--periods N` is up-to-N" notes matched reality exactly).

### Grounding (probed live 2026-06-02)

Income-statement `to_dataframe()` row counts, and rows surviving a headline filter
(`dimension==False & is_breakdown==False & abstract==False & has-value`):

| Filer | Standard | Total rows | Headline rows | Dimensional rows dropped |
|---|---|---|---|---|
| AAPL | US-GAAP | 47 | 15 | 29 |
| GRRR | IFRS (20-F) | 101 | 27 | 70 |

So the headline filter is a ~70% row cut and works identically for IFRS. The IFRS concepts
are `ifrs-full_*`; the headline filter keeps every *real* line, dropping only dimensional
breakdowns and abstract headers.

## Core idea — one backbone, three features

A shared **per-period headline extractor** turns a statement DataFrame into the real line
items across periods, each annotated with a **canonical key** when the concept is
recognized. Compact financials, multi-period ratios, and normalized labels all read from it.

## 1. `financials` — compact by default

- **Default output** is the headline set: rows where `dimension`/`is_breakdown`/`abstract`
  are false and at least one period value is present. Each row:
  ```json
  { "label": "Net income", "concept": "us-gaap_NetIncomeLoss",
    "canonical": "net_income", "2025-09-27 (FY)": 112010000000.0, "...": "..." }
  ```
  ~15 rows (AAPL) / ~27 (GRRR), bounded by `--periods` columns.
- **`--full`** restores today's complete dump (dimensional/segment/geography rows included).
  `--full` is the chosen flag name.
- **Markdown:** `--markdown` renders the headline lines as a table; under `--full` it renders
  the complete statement table.
- `query` echo gains `"full": <bool>` so the caller knows which view it received.

## 2. Multi-period ratios

`--ratios` returns a **per-period list**, newest-first:
```json
"ratios": [
  { "period": "2025-09-27 (FY)", "gross_margin": 0.46, "operating_margin": 0.32,
    "net_margin": 0.27, "return_on_equity": 1.52, "return_on_assets": 0.31,
    "current_ratio": 0.89, "debt_to_equity": 3.87, "debt_to_assets": 0.79,
    "fcf_margin": 0.30, "revenue_growth": 0.06 },
  { "period": "2024-09-28 (FY)", "...": "..." }
]
```

- Computed from the per-period canonical values extracted from the income, balance, and
  cashflow statements (replaces the latest-only `get_financial_metrics()` path from PR #3).
- A ratio is **omitted for a period** when its inputs are missing.
- Liabilities still derived via the accounting identity **Assets − Equity** (the PR #3 fix),
  now applied per period.
- `revenue_growth` for a period = (revenue − prior-period revenue) / prior-period revenue;
  omitted for the oldest period (no prior).
- This is a breaking shape change to `data.ratios` (object → list). Acceptable given the
  tool's age; called out explicitly.

## 3. Canonical GAAP/IFRS normalization

- A curated map in a new module `src/edgar_research/concepts.py`:
  `CANONICAL: dict[str, str]` from headline `us-gaap_*` **and** `ifrs-full_*` concepts to
  canonical names, covering the core P&L / balance / cashflow lines:
  `revenue, cost_of_revenue, gross_profit, operating_income, operating_expenses,
  research_and_development, net_income, total_assets, total_liabilities,
  stockholders_equity, current_assets, current_liabilities, operating_cash_flow,
  capital_expenditures, free_cash_flow, eps_basic, eps_diluted` (extend as needed).
- Each canonical name maps from one or more source concepts (alias lists), since GAAP and
  IFRS tag the same idea differently.
- Used for (a) the `canonical` field on headline rows and (b) selecting ratio inputs.
- **Unmapped concepts degrade gracefully**: `canonical: null`, row still shown. The map is
  enrichment, never a filter — no fragile dependence on full coverage, no maintenance
  treadmill.

## 4. `read` — auto-detect the annual report

- When `--form` is omitted, `read` selects the **latest annual report** among
  `{10-K, 20-F, 40-F}` (most recent by filing date across those forms).
- `--form X` overrides (today's behavior).
- Section extraction is unchanged and already robust: the existing `_available_sections`
  error and `--section full` fallback handle a 20-F's differing structure (its filing object
  may expose different/fewer section accessors).
- A small pure helper `_pick_latest_annual(filings)` makes the selection unit-testable.

## 5. Ergonomics

- **`--markdown` accepted before or after the subcommand** — add it as a shared argument on
  each subparser (via an argparse parent parser) in addition to the top-level parser, and
  OR the two results so position doesn't matter.
- **SKILL.md note:** the first `uvx --from git+… edgar-research …` call takes ~15–20s to
  fetch/build deps; subsequent calls are cached.

## Out of scope (YAGNI)

- A general jq-style `--fields "Revenue,Net income"` selector (feedback #4) — the compact
  default removes the main need; revisit if explicitly requested.
- Normalization beyond the curated headline set — unmapped lines already degrade gracefully.

## File structure

```
src/edgar_research/
  concepts.py                 # NEW: CANONICAL alias map + concept->canonical lookup
  commands/
    financials.py             # CHANGED: headline extractor, compact default + --full,
                              #          per-period ratios, canonical annotation
    read.py                   # CHANGED: _pick_latest_annual + auto-form default
  cli.py                      # CHANGED: --full on financials; --markdown accepted anywhere
tests/
  test_concepts.py            # NEW: canonical lookup (GAAP + IFRS), unmapped -> None
  test_financials_headline.py # NEW: headline filtering + per-period ratio math (synthetic)
  test_read_form_select.py    # NEW: _pick_latest_annual across a synthetic filings list
  test_cli_smoke.py           # CHANGED: --markdown-after-subcommand + --full parse
  test_live.py                # CHANGED: compact-default, --full, per-period ratios, GRRR 20-F
README.md                     # CHANGED
skills/edgar-research/SKILL.md # CHANGED
```

## Testing strategy

- **Deterministic (no network):**
  - `concepts.py`: canonical lookup resolves both a us-gaap and an ifrs-full concept to the
    same canonical name; unknown concept → `None`.
  - headline filtering: a synthetic statement DataFrame with abstract, dimensional, and
    all-null rows yields only the real line items, canonical-annotated.
  - per-period ratio math: synthetic per-period canonical values → expected ratios, with the
    Assets−Equity identity and per-period `revenue_growth`; missing inputs omitted.
  - `_pick_latest_annual`: from a synthetic list of (form, date) filings, picks the most
    recent among {10-K, 20-F, 40-F}, ignoring other forms; returns None when none present.
  - CLI smoke: `financials AAPL --full --markdown` and `financials --markdown AAPL` both
    parse; `--full` defaults false.
- **Live (opt-in, RUN_LIVE=1):**
  - `financials AAPL` (GAAP) and `financials GRRR` (IFRS/20-F) default to compact headline
    rows carrying `canonical` labels; `--full` returns strictly more rows.
  - `financials AAPL --ratios` returns a per-period list with sane `net_margin` per period.
  - `read GRRR` with no `--form` resolves the latest 20-F and returns text.

## Docs

`SKILL.md` and `README.md` updated for: compact-default + `--full`, per-period ratios,
canonical labels, `read` auto-form, `--markdown` anywhere, and the uvx timing note; refresh
the recommended sequence (drop the explicit `--form 10-K` from the `read` step) and gotchas.

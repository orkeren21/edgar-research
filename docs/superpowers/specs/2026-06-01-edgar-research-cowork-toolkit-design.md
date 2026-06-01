# Design: `edgar-research` — a Cowork-facing SEC EDGAR toolkit

**Date:** 2026-06-01
**Status:** Approved (design phase)

## Purpose

A small Python CLI that wraps [`edgartools`](https://github.com/dgunning/edgartools)
into a stable, agent-friendly interface so Claude Cowork can investigate potential
investments without writing ad-hoc `edgartools` code each time.

The CLI is **JSON-first**, built from **granular subcommands**, and deliberately keeps
investigation *orchestration* out of code — that lives in the Cowork skill (a later phase,
authored with the writing-skills skill). This project produces the CLI plus a README
documenting each command's contract, which that skill will wrap.

### Why a wrapper instead of letting the agent write `edgartools` directly

- **Deterministic contract.** Every command emits the same JSON envelope, so the agent
  reasons over data instead of re-deriving the library API each call.
- **No API drift in the agent's head.** Method names, identity setup, rate-limit and
  DataFrame-serialization gotchas are handled once, here.
- **Cleanest possible skill.** A documented CLI with `--help` is far easier to teach than
  "write correct edgartools Python."

## Validated API facts (probed live 2026-06-01, not assumed)

Confirmed against `edgartools` in an ephemeral `uv` environment (`set_identity` +
`Company("AAPL")` round-trip succeeded):

- `Company(ticker_or_cik)` → `.name`, `.cik`.
- `company.get_financials()` exposes `income_statement()`, `balance_sheet()`,
  `cash_flow_statement()`, `comprehensive_income()`, `statement_of_equity()`, plus
  convenience getters (`get_revenue`, `get_net_income`, `get_free_cash_flow`,
  `get_operating_cash_flow`, `get_capital_expenditures`, `get_financial_metrics`, …).
- Statement objects have **built-in** `to_dataframe()`, `to_markdown()`,
  `calculate_ratios()`, `analyze_trends()`, `get_raw_data()`, `text()` — these back both
  output modes directly.
- `company.get_filings(form=...)` → `EntityFilings`; `.latest()` →`EntityFiling` with
  `accession_no`, `filing_date`, `form`, `filing_url`, `text()`, `attachments`, `obj()`.
- Form 4 object (`.obj()`) exposes `to_dataframe()`, `get_transaction_activities()`,
  `get_ownership_summary()`, `common_stock_purchases`, `common_stock_sales`,
  `insider_name`, `issuer`.
- Top-level full-text search: `search_filings(...)` / `search(...)` (EDGAR Full-Text
  Search, a.k.a. `EFTSSearch`).

Nothing in this design is hypothetical.

## Project & tooling

- **New git repo:** `~/Projects/edgar-research`. *Not* a fork of edgartools — edgartools is
  a dependency.
- **Managed by `uv`.** Single direct dependency: `edgartools` (transitively pulls pandas).
- **CLI framework:** `argparse` (zero extra deps; clean `--help` the agent can read).
- **Invocation:** console script → `uv run edgar-research <subcommand> …`.

## Subcommands (cover all four prioritized workflows)

| Command | Purpose | Workflow |
|---|---|---|
| `company TICKER` | Identity card: name, CIK, ticker, industry/SIC, exchange, fiscal-year-end, latest filing dates | Fundamentals |
| `financials TICKER [--statement income\|balance\|cashflow\|all] [--periods N] [--ratios]` | Multi-period statements (periods = columns, line-items = rows) + optional derived ratios | Fundamentals |
| `filings TICKER [--form 10-K] [--limit N] [--since DATE]` | List available filings with metadata (form, date, accession, URL) | Filing retrieval |
| `read TICKER --form 10-K [--section risk-factors\|mda\|business] [--latest]` | Extract readable filing text / a specific section for the agent to analyze | Filing reading |
| `insiders TICKER [--limit N] [--since DATE] [--net]` | Recent Form 3/4/5 transactions flattened to rows; `--net` = aggregated buy/sell summary | Insider activity |
| `holdings INSTITUTION [--limit N]` | Latest 13F-HR portfolio of an *institution* (e.g. Berkshire) as rows (name, cusip, value, shares, %) | Fund activity |
| `search QUERY [--form ...] [--date-range ...] [--limit N]` | Full-text EDGAR search → matching filings + snippets, for theme/competitor discovery | Full-text search |

### Per-command notes

- **`financials`** — statements rendered via the Statement object's native
  `to_dataframe()` (JSON) / `to_markdown()` (readable). `--ratios` layers in
  `calculate_ratios()` / `get_financial_metrics()` (margins, growth, leverage, FCF). Default
  `--periods` chosen for a useful multi-year trend (e.g. 4–5).
- **`read`** — large section text is chunked and returned with a `truncated` flag and length,
  so the agent knows when it has a partial view. Section extraction uses the form object's
  item accessors where available, otherwise falls back to whole-filing `text()`.
- **`holdings`** — 13F is **filer-centric**: it returns an *institution's* portfolio, keyed by
  that institution's identifier. The reverse ("which funds hold AAPL?") has no clean
  edgartools primitive and is **out of scope**.
- **`insiders`** — `--net` aggregates buys vs. sells (count, shares, value) as a quick
  conviction signal; without it, returns the flattened transaction rows.

## Output contract (the key interface)

- **Default — JSON envelope to stdout:**
  ```json
  {
    "ok": true,
    "command": "financials",
    "query": { "ticker": "AAPL", "statement": "income", "periods": 4 },
    "data": { },
    "meta": { "source": "SEC EDGAR", "as_of": "<filing date(s)>" }
  }
  ```
- **Errors — to stdout + non-zero exit code:**
  ```json
  { "ok": false, "error": { "type": "company_not_found", "message": "..." } }
  ```
  Non-zero exit lets the agent reliably detect failure.
- **`--markdown` flag** → human-readable tables (reuses edgartools' native `to_markdown()`
  where available) for when a human runs it directly.
- A central `output.py` serializes DataFrames → JSON identically for every command
  (NaN → null, dates → ISO 8601), so output shape is uniform.

## Cross-cutting concerns

- **SEC identity.** Read from the `EDGAR_IDENTITY` env var (the user's email is the
  documented default); call `set_identity()` once at startup. Missing identity → a clear,
  typed error, not a crash.
- **Error handling.** Map `CompanyNotFoundError`, no-filings-of-requested-form,
  network/429/timeout, and missing-identity into typed structured errors + exit codes.
- **Network requirement.** Needs outbound HTTPS to `sec.gov`. This is a prerequisite the
  future skill must state. Rate limiting and local caching are handled by edgartools.

## Project layout

```
edgar-research/
  pyproject.toml              # dep: edgartools; console script edgar-research
  README.md                   # per-command contract (feeds the future skill)
  src/edgar_research/
    __init__.py
    cli.py                    # argparse dispatch + identity + output/error wrapping
    commands/
      __init__.py
      company.py
      financials.py
      filings.py
      read.py
      insiders.py
      holdings.py
      search.py
    output.py                 # JSON envelope + DataFrame serializer + markdown helpers
    errors.py                 # error types -> structured output + exit codes
  tests/
    test_output.py            # serializer / envelope / error-mapping unit tests (no network)
    test_cli_smoke.py         # argparse wiring + --help + error envelopes
    test_live.py              # opt-in @live SEC tests vs AAPL (skipped by default)
```

## Testing strategy

- **TDD for the deterministic core:** `output.py` serializer + `errors.py` mapping — pure,
  no network, fully reproducible.
- **Smoke tests** for argparse wiring, `--help`, and error envelopes.
- **Opt-in live tests** (pytest marker, skipped by default) that hit SEC for AAPL to catch
  edgartools API drift; run manually, not in normal CI.
- **Manual end-to-end:** run every subcommand against AAPL, an institution (Berkshire),
  and a search term; eyeball both JSON and `--markdown`.

## Explicitly out of scope (YAGNI)

- Composite `brief` one-shot command (deferred — orchestration lives in skill prose; can
  become a later "Approach C" if the granular layer proves insufficient).
- Reverse institutional-ownership lookup ("who holds ticker X").
- Extra caching beyond edgartools' built-in; non-EDGAR data sources.
- **The Cowork skill itself** — the next phase, driven by the writing-skills skill, which
  wraps this CLI's documented contract and adds the recommended investigation sequence.

## Relationship to the eventual Cowork skill

This project ships the CLI + a README documenting each command's input/output contract.
The writing-skills phase then produces a Cowork skill that adds:

1. Install/prereqs (`uv`, `EDGAR_IDENTITY`, network to `sec.gov`).
2. A per-command cheat-sheet.
3. The recommended end-to-end "investigate a potential investment" sequence — the
   orchestration Approach A intentionally keeps out of code so the agent can adapt it
   per company.

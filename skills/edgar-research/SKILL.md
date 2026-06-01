---
name: edgar-research
description: Use when investigating a public company as a potential investment, or when you need SEC EDGAR data for a US-listed company — financial statements, 10-K/10-Q/8-K filings, risk factors / MD&A, insider (Form 4) trades, 13F institutional holdings, or full-text filing search. Symptoms include "is TICKER a good investment", "pull NVDA's financials", "what are the risk factors", "insider buying or selling", "who holds this stock".
---

# edgar-research

## Overview

`edgar-research` is a CLI that pulls **SEC EDGAR** data as clean JSON (it wraps the
`edgartools` library). It returns **primary-source data, not conclusions** — you do the
analysis. Reach for it to ground investment research in actual filings instead of
web hearsay.

## Setup (do this before the first command)

- **Identity is required.** SEC requires a contact email as a User-Agent. Set
  `EDGAR_IDENTITY` (an env var, or a `.env` file in the working dir). If it is unset,
  **every command fails with `identity_missing` (exit 2)** — there is no default. See the
  repo README for `.env` setup.
- **Invocation:** if `edgar-research` is on your PATH, run `edgar-research <command> …`.
  Otherwise (e.g. in Cowork, no local clone) run it with **no install**:
  `uvx --from git+https://github.com/orkeren21/edgar-research.git edgar-research <command> …`.
  Requires outbound network to `sec.gov`.
- **Output:** JSON by default — read the `data` field and reason over it. Add the global
  `--markdown` flag *before* the subcommand for human-readable tables.

## Commands

| Command | Use it to… |
|---|---|
| `company TICKER` | Confirm the entity; get CIK, industry, fiscal year, recent filings |
| `financials TICKER [--statement income\|balance\|cashflow\|all] [--periods N] [--ratios]` | Pull multi-period statements (+ ratios) — the core "is this a good business?" data |
| `filings TICKER [--form 10-K] [--limit N] [--since YYYY-MM-DD]` | Discover which filings exist, with dates + URLs |
| `read TICKER [--form 10-K] [--section risk-factors\|mda\|business\|full] [--max-chars N]` | Read filing prose — risk factors, MD&A, business overview |
| `insiders TICKER [--limit N] [--since YYYY-MM-DD] [--net]` | Form 4 insider buys/sells; `--net` aggregates by transaction type |
| `holdings INSTITUTION [--limit N]` | An institution's latest 13F portfolio (filer-centric, e.g. `BRK-A`) |
| `search "QUERY" [--form 10-K] [--date-range A:B] [--limit N]` | Full-text search across all EDGAR filings since 1994 |

Run any command with `--help` for exact flags.

## Recommended sequence for "is TICKER a good investment?"

1. `company TICKER` — confirm you have the right entity.
2. `financials TICKER --statement all --periods 5 --ratios` — multi-period line items, plus
   `--ratios` adds latest-period ratios (operating & net margin, ROE, ROA, current ratio,
   debt-to-equity, debt-to-assets, FCF margin when available, revenue growth) to the JSON.
3. `read TICKER --section risk-factors`, then `--section mda` — what management flags and
   explains. If a section is unavailable the error lists which ones are; or use `--section full`.
4. `insiders TICKER --limit 20 --net` — conviction signal (net buying vs selling).
5. Synthesize: business quality + trajectory + risks + insider behavior → assessment.

Use `filings` to locate a specific document, `search` to find filings by theme/competitor,
and `holdings` to inspect a fund's portfolio. Each command is one focused fetch — compose
them; don't expect one command to do everything.

## Gotchas

| Pitfall | Reality |
|---|---|
| Skipping identity setup | First call returns `identity_missing` (exit 2). Set `EDGAR_IDENTITY` first. |
| `--ratios` scope | Adds **latest-period** ratios to JSON `data.ratios` (not the `--markdown` tables); a ratio is omitted when its inputs are missing. For multi-period trends, read the statement rows. |
| A `--section` returns `usage_error` | That section isn't in this filing. The error lists which sections ARE available — retry with one, or use `--section full`. |
| `--periods N` returns fewer than N | `N` is "up to N most recent" — bounded by available XBRL periods. |
| Reading a long section | `read` truncates at `--max-chars`; the JSON `truncated`/`length` fields tell you if there's more. |
| Using `holdings` for "who owns TICKER?" | 13F is filer-centric: it returns an *institution's* portfolio, not the holders of a stock. |
| Bad/unknown ticker | Returns `company_not_found` (exit 3) — check the symbol or pass a CIK. |

## Error contract

Failures print `{"ok": false, "error": {"type": ..., "message": ...}}` and a non-zero exit:
`identity_missing` (2), `company_not_found` (3), `no_filings_found` (4),
`network_error` (5), `usage_error` (6), `unexpected_error` (1).

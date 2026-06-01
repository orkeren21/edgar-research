# edgar-research

A small CLI that wraps [`edgartools`](https://github.com/dgunning/edgartools) into
stable, JSON-first commands for investigating potential investments. Built to be driven
by an agent (Claude Cowork); a human can add `--markdown` for readable output.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) installed.
- Outbound HTTPS to `sec.gov` (the SEC EDGAR API).
- A contact email in `EDGAR_IDENTITY` (SEC requires a User-Agent). Defaults to a
  baked-in fallback if unset.

## Install & run

```bash
uv sync
export EDGAR_IDENTITY="you@example.com"
uv run edgar-research company AAPL
```

## Output contract

Every command prints a JSON envelope to stdout:

```json
{ "ok": true, "command": "...", "query": { }, "data": { },
  "meta": { "source": "SEC EDGAR" } }
```

On failure: `{ "ok": false, "error": { "type": "...", "message": "..." } }` plus a
non-zero exit code. Add `--markdown` (before the subcommand) for human-readable tables.

Error types / exit codes: `identity_missing` (2), `company_not_found` (3),
`no_filings_found` (4), `network_error` (5), `usage_error` (6), `unexpected_error` (1).

## Commands

| Command | Description |
|---|---|
| `company TICKER` | Identity card: name, CIK, tickers, industry, SIC, fiscal-year-end, recent filings. |
| `financials TICKER [--statement income\|balance\|cashflow\|all] [--periods N] [--ratios]` | Multi-period statements (periods as columns) + optional ratios. |
| `filings TICKER [--form 10-K] [--limit N] [--since YYYY-MM-DD]` | List filings with metadata + URLs. |
| `read TICKER [--form 10-K] [--section risk-factors\|mda\|business\|full] [--max-chars N]` | Extract readable filing text (chunked with a `truncated` flag). |
| `insiders TICKER [--limit N] [--since YYYY-MM-DD] [--net]` | Recent Form 4 transactions; `--net` aggregates by transaction type. |
| `holdings INSTITUTION [--limit N]` | Latest 13F-HR portfolio of an institutional filer (top N by value). |
| `search QUERY [--form ...] [--date-range YYYY-MM-DD:YYYY-MM-DD] [--limit N]` | Full-text EDGAR search. |

### Notes & limitations

- `holdings` is filer-centric: it returns an institution's portfolio. The reverse
  ("which funds hold AAPL?") is not supported.
- `financials` defaults to 4 periods. `--ratios` is best-effort and may return
  `{"error": ...}` for entities where edgartools can't compute them.
- For `filings` and `insiders`, `--limit` caps how many of the most-recent filings are
  scanned; `--since` then filters within that window. Filings are returned newest-first,
  so the result is the most-recent matching filings (raise `--limit` to look further back).
- Rate limiting and local caching are handled by `edgartools`.

## Tests

```bash
uv run pytest                 # deterministic suite (no network)
RUN_LIVE=1 uv run pytest      # also runs live SEC tests
```

# edgar-research

A small CLI that wraps [`edgartools`](https://github.com/dgunning/edgartools) into
stable, JSON-first commands for investigating potential investments. Built to be driven
by an agent (Claude Cowork); a human can add `--markdown` for readable output.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) installed.
- Outbound HTTPS to `sec.gov` (the SEC EDGAR API).
- A contact email in `EDGAR_IDENTITY` (SEC requires a User-Agent identifying the
  requester). Provide it via the environment or a local `.env` file — there is **no
  baked-in default**; commands fail with `identity_missing` (exit 2) if it is unset.

## Install & run

```bash
uv sync
cp .env.example .env        # then edit .env and set EDGAR_IDENTITY=you@example.com
# or, instead of .env:      export EDGAR_IDENTITY="you@example.com"
uv run edgar-research company AAPL
```

`.env` is gitignored; real environment variables take precedence over it.

## Output contract

Every command prints a JSON envelope to stdout:

```json
{ "ok": true, "command": "...", "query": { }, "data": { },
  "meta": { "source": "SEC EDGAR" } }
```

On failure: `{ "ok": false, "error": { "type": "...", "message": "..." } }` plus a
non-zero exit code. Add `--markdown` for human-readable tables.
`--markdown` may be placed before or after the subcommand.

Error types / exit codes: `identity_missing` (2), `company_not_found` (3),
`no_filings_found` (4), `network_error` (5), `usage_error` (6), `unexpected_error` (1).

## Commands

| Command | Description |
|---|---|
| `company TICKER` | Identity card: name, CIK, tickers, industry, SIC, fiscal-year-end, recent filings. |
| `financials TICKER [--statement income\|balance\|cashflow\|all] [--periods N] [--ratios] [--full]` | Compact headline statements (`--full` for the complete dump) + optional per-period ratios. |
| `filings TICKER [--form 10-K] [--limit N] [--since YYYY-MM-DD]` | List filings with metadata + URLs. |
| `read TICKER [--form 10-K] [--section risk-factors\|mda\|business\|full] [--max-chars N]` | Read filing prose; defaults to the latest annual report (10-K/20-F/40-F) when `--form` is omitted. |
| `insiders TICKER [--limit N] [--since YYYY-MM-DD] [--net]` | Recent Form 4 transactions; `--net` aggregates by transaction type. |
| `holdings INSTITUTION [--limit N]` | Latest 13F-HR portfolio of an institutional filer (top N by value). |
| `search QUERY [--form ...] [--date-range YYYY-MM-DD:YYYY-MM-DD] [--limit N]` | Full-text EDGAR search. |

### Notes & limitations

- `holdings` is filer-centric: it returns an institution's portfolio. The reverse
  ("which funds hold AAPL?") is not supported.
- `financials` returns **compact headline lines by default** (dimensional/segment/zero rows
  dropped; each row carries a `canonical` label where recognized). Pass `--full` for the
  complete dump. `--ratios` returns a **per-period list** in `data.ratios` (gross/operating/net
  margin, ROE, ROA, current ratio, debt-to-equity, debt-to-assets, FCF margin, revenue growth),
  omitting any ratio whose inputs are missing for that period.
- `read` defaults to the latest annual report across 10-K / 20-F / 40-F when `--form` is
  omitted (so foreign private issuers work without specifying the form).
- For `filings` and `insiders`, `--limit` caps how many of the most-recent filings are
  scanned; `--since` then filters within that window. Filings are returned newest-first,
  so the result is the most-recent matching filings (raise `--limit` to look further back).
- Rate limiting and local caching are handled by `edgartools`.

## Install as a Claude Code / Cowork plugin

This repo is a single-plugin **marketplace** (`.claude-plugin/marketplace.json` +
`.claude-plugin/plugin.json`) that ships the agent skill at
[`skills/edgar-research/SKILL.md`](skills/edgar-research/SKILL.md) — it teaches the agent
*when* to reach for this CLI and *how* to drive it (setup, the seven commands, a recommended
investigation sequence, and gotchas).

### Claude Code (CLI)

```text
/plugin marketplace add orkeren21/edgar-research
/plugin install edgar-research@edgar-research
```

Restart Claude Code (or run `/reload-plugins`). The skill activates automatically when a
request matches it, and is invocable as `/edgar-research:edgar-research`. This works with
private repos too (it uses your local `gh` auth).

*(Prefer just the skill, without the plugin? Symlink it in and restart:
`ln -s "$(pwd)/skills/edgar-research" ~/.claude/skills/edgar-research`.)*

### Cowork (desktop / claude.ai)

Cowork manages plugins through its UI — **Customize → Plugins**. Add this repo
(`orkeren21/edgar-research`) as a plugin source, then install **edgar-research** and choose a
scope. Plugin management in Cowork is UI-driven and evolving, so follow the in-app flow; the
repo must be reachable by Cowork (public, or a marketplace your org admin has configured).

### Make the CLI runnable

The skill shells out to `edgar-research`. Provide it either way:

- **On PATH** (local machines): `uv tool install .` from the repo root, or
  `uv tool install git+https://github.com/orkeren21/edgar-research.git`.
- **Zero-install** (Cowork sandbox / no clone): the skill runs it via
  `uvx --from git+https://github.com/orkeren21/edgar-research.git edgar-research …` —
  no setup beyond `uv` + outbound network.

### Set your SEC identity

`EDGAR_IDENTITY` is required (no default). For skill use across directories, set it
persistently — `export EDGAR_IDENTITY="you@example.com"` in your shell profile or your
Claude Code / Cowork environment settings — or prefix individual commands
(`EDGAR_IDENTITY=you@example.com edgar-research …`).

## Tests

```bash
uv run pytest                 # deterministic suite (no network)
RUN_LIVE=1 uv run pytest      # also runs live SEC tests
```

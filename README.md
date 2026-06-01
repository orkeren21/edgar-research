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
- `financials` defaults to 4 periods. `--ratios` is best-effort and **frequently returns
  empty** (edgartools doesn't populate per-statement ratios for many companies) — derive
  margins / growth / FCF from the statement line items instead.
- For `filings` and `insiders`, `--limit` caps how many of the most-recent filings are
  scanned; `--since` then filters within that window. Filings are returned newest-first,
  so the result is the most-recent matching filings (raise `--limit` to look further back).
- Rate limiting and local caching are handled by `edgartools`.

## Use as a Claude Code / Cowork skill

This repo ships an agent skill at [`skills/edgar-research/SKILL.md`](skills/edgar-research/SKILL.md)
that teaches Claude Code / Cowork *when* to reach for this CLI and *how* to drive it — setup,
the seven commands, a recommended investigation sequence, and the gotchas.

### 1. Put the CLI on your PATH

The skill invokes the bare `edgar-research` command, so install it as a tool:

```bash
uv tool install .            # from the repo root (or: uv tool install /path/to/edgar-research)
edgar-research --help        # confirm it resolves
```

Because the skill runs from arbitrary directories, set your SEC identity as a **persistent**
environment variable — a repo-local `.env` is only picked up when you run from that repo:

```bash
echo 'export EDGAR_IDENTITY="you@example.com"' >> ~/.zshrc   # or ~/.bashrc
```

### 2. Claude Code (CLI)

Symlink (or copy) the skill folder into a skills directory, then restart Claude Code:

```bash
# Personal — available in every project:
ln -s "$(pwd)/skills/edgar-research" ~/.claude/skills/edgar-research

# …or project-scoped — committed to a repo and shared with anyone who clones it:
mkdir -p /path/to/your-project/.claude/skills
ln -s "$(pwd)/skills/edgar-research" /path/to/your-project/.claude/skills/edgar-research
```

Claude Code auto-discovers skills on startup and activates this one when your request matches
its description (you can also invoke it explicitly as `/edgar-research`). List skills with `/help`.

### 3. Cowork (claude.ai / desktop)

Cowork uses the same Agent Skills format. Add this skill through Cowork's **Skills / Plugins**
feature — the most portable path is to package this repo as a plugin and install it from your
Cowork session. The exact UI and commands evolve between Cowork versions, so follow the in-app
flow; the skill content to register is
[`skills/edgar-research/SKILL.md`](skills/edgar-research/SKILL.md), and the `edgar-research`
CLI must be reachable in Cowork's environment (step 1).

## Tests

```bash
uv run pytest                 # deterministic suite (no network)
RUN_LIVE=1 uv run pytest      # also runs live SEC tests
```

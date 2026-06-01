"""JSON envelope, DataFrame serialization, and markdown rendering."""
from __future__ import annotations

import datetime as _dt
import json
import math
from typing import Any

import numpy as np
import pandas as pd

SOURCE = "SEC EDGAR"


def sanitize(value: Any) -> Any:
    """Convert pandas/numpy scalars into JSON-safe Python values."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def dataframe_to_records(df: pd.DataFrame, columns: list[str] | None = None,
                         rename: dict[str, str] | None = None) -> list[dict]:
    rename = rename or {}
    cols = [c for c in (columns or list(df.columns)) if c in df.columns]
    records = []
    for _, row in df.iterrows():
        records.append({rename.get(c, c): sanitize(row[c]) for c in cols})
    return records


def success(command: str, query: dict, data: Any, meta: dict | None = None) -> dict:
    return {
        "ok": True,
        "command": command,
        "query": query,
        "data": data,
        "meta": {"source": SOURCE, **(meta or {})},
    }


def failure(error_type: str, message: str) -> dict:
    return {"ok": False, "error": {"type": error_type, "message": message}}


def records_to_markdown(records: list[dict], title: str | None = None) -> str:
    lines: list[str] = []
    if title:
        lines.append(f"### {title}\n")
    if not records:
        lines.append("_(no rows)_")
        return "\n".join(lines)
    headers = list(records[0].keys())
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for rec in records:
        cells = ["" if rec.get(h) is None else str(rec.get(h)).replace("|", "\\|") for h in headers]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def clean(obj: Any) -> Any:
    """Recursively make a payload JSON-safe (dicts, lists, and scalars)."""
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    return sanitize(obj)


def render(payload: dict, markdown: bool = False, markdown_text: str | None = None) -> str:
    if not markdown:
        return json.dumps(clean(payload), indent=2, default=str)
    if not payload.get("ok", False):
        err = payload.get("error", {})
        return f"**Error ({err.get('type', 'error')}):** {err.get('message', '')}"
    if markdown_text is not None:
        return markdown_text
    return "_(no markdown representation; use JSON output)_"

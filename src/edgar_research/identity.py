"""Resolve and apply the SEC EDGAR identity (User-Agent email)."""
from __future__ import annotations

import os

from edgar import set_identity

from .errors import IdentityError

DEFAULT_IDENTITY = "or.keren21@gmail.com"


def resolve_identity(env: dict | None = None) -> str:
    env = os.environ if env is None else env
    ident = env.get("EDGAR_IDENTITY") or DEFAULT_IDENTITY
    if not ident or "@" not in ident:
        raise IdentityError(
            "EDGAR_IDENTITY must be a contact email (SEC requires a User-Agent). "
            f"Got: {ident!r}"
        )
    return ident


def apply_identity(env: dict | None = None) -> str:
    ident = resolve_identity(env)
    set_identity(ident)
    return ident

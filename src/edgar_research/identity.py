"""Resolve and apply the SEC EDGAR identity (User-Agent email)."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from edgar import set_identity

from .errors import IdentityError


def resolve_identity(env: dict | None = None) -> str:
    env = os.environ if env is None else env
    ident = env.get("EDGAR_IDENTITY")
    if not ident or "@" not in ident:
        raise IdentityError(
            "EDGAR_IDENTITY is not set to a contact email. SEC requires a User-Agent "
            "identifying the requester. Set it in your environment or a local .env file "
            "(see .env.example), e.g. EDGAR_IDENTITY=you@example.com. "
            f"Got: {ident!r}"
        )
    return ident


def apply_identity(env: dict | None = None) -> str:
    """Load a local .env (if present), then resolve and apply the SEC identity.

    Real environment variables take precedence over values in .env. When ``env``
    is passed explicitly (e.g. in tests), no .env loading occurs.
    """
    if env is None:
        load_dotenv()  # fills os.environ from .env without overriding real env vars
        env = os.environ
    ident = resolve_identity(env)
    set_identity(ident)
    return ident

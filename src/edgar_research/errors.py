"""Typed errors mapped to structured output + process exit codes."""
from __future__ import annotations


class EdgarResearchError(Exception):
    error_type = "error"
    exit_code = 1

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class IdentityError(EdgarResearchError):
    error_type = "identity_missing"
    exit_code = 2


class CompanyNotFound(EdgarResearchError):
    error_type = "company_not_found"
    exit_code = 3


class NoFilingsFound(EdgarResearchError):
    error_type = "no_filings_found"
    exit_code = 4


class NetworkError(EdgarResearchError):
    error_type = "network_error"
    exit_code = 5


class UsageError(EdgarResearchError):
    error_type = "usage_error"
    exit_code = 6


class UnexpectedError(EdgarResearchError):
    error_type = "unexpected_error"
    exit_code = 1


_NETWORK_EXC_NAMES = {
    "ConnectionError", "Timeout", "ConnectTimeout", "ReadTimeout",
    "HTTPError", "RequestException", "TooManyRedirects", "ConnectionResetError",
}


def classify(exc: Exception) -> EdgarResearchError:
    """Map any exception to a typed EdgarResearchError (passthrough if already one)."""
    if isinstance(exc, EdgarResearchError):
        return exc
    name = type(exc).__name__
    if name == "CompanyNotFoundError":
        return CompanyNotFound(str(exc) or "Company not found.")
    if isinstance(exc, (ConnectionError, TimeoutError)) or name in _NETWORK_EXC_NAMES:
        return NetworkError(str(exc) or "Network error talking to SEC EDGAR.")
    return UnexpectedError(f"{name}: {exc}")

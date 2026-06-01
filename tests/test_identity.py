import pytest

from edgar_research import identity
from edgar_research.errors import IdentityError


def test_resolve_from_env():
    assert identity.resolve_identity({"EDGAR_IDENTITY": "a@b.com"}) == "a@b.com"


def test_resolve_default_when_missing():
    assert identity.resolve_identity({}) == identity.DEFAULT_IDENTITY


def test_resolve_rejects_garbage():
    with pytest.raises(IdentityError):
        identity.resolve_identity({"EDGAR_IDENTITY": "not-an-email"})

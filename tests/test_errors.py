from edgar_research import errors


def test_classify_passthrough():
    e = errors.IdentityError("x")
    assert errors.classify(e) is e
    assert e.error_type == "identity_missing" and e.exit_code == 2


def test_classify_network():
    assert errors.classify(ConnectionError("x")).error_type == "network_error"
    assert errors.classify(TimeoutError("x")).exit_code == 5


def test_classify_company_not_found_by_name():
    class CompanyNotFoundError(Exception):
        pass
    err = errors.classify(CompanyNotFoundError("AAPL?"))
    assert err.error_type == "company_not_found" and err.exit_code == 3


def test_classify_unexpected():
    err = errors.classify(ValueError("boom"))
    assert err.error_type == "unexpected_error" and err.exit_code == 1

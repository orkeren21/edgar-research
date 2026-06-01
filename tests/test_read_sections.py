from edgar_research.commands import read


class _FakeFiling:
    def __init__(self, **attrs):
        for key, value in attrs.items():
            setattr(self, key, value)


def test_available_sections_lists_present_only():
    obj = _FakeFiling(risk_factors=None, management_discussion="MD&A text", business="")
    assert read._available_sections(obj) == ["mda"]


def test_available_sections_all_present():
    obj = _FakeFiling(risk_factors="rf", management_discussion="md", business="biz")
    assert read._available_sections(obj) == ["risk-factors", "mda", "business"]


def test_available_sections_none_present():
    obj = _FakeFiling(risk_factors=None, management_discussion=None, business=None)
    assert read._available_sections(obj) == []

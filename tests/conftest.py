import os
import pytest


def pytest_collection_modifyitems(config, items):
    """Skip @live tests unless RUN_LIVE=1 is set in the environment."""
    if os.environ.get("RUN_LIVE") == "1":
        return
    skip_live = pytest.mark.skip(reason="live SEC test; set RUN_LIVE=1 to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)

import os

import pytest


def pytest_collection_modifyitems(config, items):
    """Gate @live tests.

    - Off unless RUN_LIVE=1.
    - When RUN_LIVE=1 but no SEC identity is configured (env var or .env),
      skip them with guidance instead of failing confusingly.
    """
    live_items = [it for it in items if "live" in it.keywords]
    if not live_items:
        return

    if os.environ.get("RUN_LIVE") != "1":
        skip = pytest.mark.skip(reason="live SEC test; set RUN_LIVE=1 to run")
        for it in live_items:
            it.add_marker(skip)
        return

    # RUN_LIVE=1: live tests need a SEC identity (real env var or a local .env).
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("EDGAR_IDENTITY"):
        skip = pytest.mark.skip(
            reason="live tests need EDGAR_IDENTITY (set the env var or a local .env)"
        )
        for it in live_items:
            it.add_marker(skip)

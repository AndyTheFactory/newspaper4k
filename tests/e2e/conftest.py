import os

import pytest

pytestmark = pytest.mark.e2e


def pytest_runtest_setup(item):
    """Skip integration/e2e tests automatically in CI."""
    if "GITHUB_ACTIONS" in os.environ:
        pytest.skip("Skipping e2e tests in GitHub Actions")

"""Pytest Fixtures."""

import os
import platform

import pytest


def pytest_collection_finish(session):
    pass

@pytest.fixture()
def driver_name() -> str:
    """Return name of the driver to be tested."""
    return "custom-kubevirt"

"""Unit tests."""

from molecule import api
from molecule_plugins.kubevirt.driver import KubeVirt


def test_kubevirt_driver_is_detected():
    """Asserts that molecule recognizes the driver."""
    assert any(str(d) == "kubevirt" for d in api.drivers())


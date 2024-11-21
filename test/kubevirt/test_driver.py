"""Unit tests."""

from molecule import api
from molecule.config import Config

from molecule_plugins.kubevirt.driver import KubeVirt
import pytest

@pytest.fixture
def temp_molecule_config(tmp_path):
    """Fixture to create a temporary Molecule configuration file."""
    content = """
dependency:
  name: galaxy
driver:
  name: custom-kubevirt
  kubeconfig: kubeconfig

platforms:
  - name: default
    rootFsStorageClass: "longhorn-image-pqsf2"
    rootFsName: root-fs
    namespace: harvester-public
    """
    temp_file = tmp_path / "molecule.yml"
    temp_file.write_text(content)
    temp_kubeconfig = tmp_path / "kubeconfig"
    temp_kubeconfig.write_text("---")
    config = Config(molecule_file=str(temp_file))

    return config

def test_kubevirt_driver_is_detected():
    """Asserts that molecule recognizes the driver."""
    assert any(str(d) == "custom-kubevirt" for d in api.drivers())


def test_kubevirt_driver():
    KubeVirt()

def test_kubevirt_driver_config(temp_molecule_config):
    kv = KubeVirt(config=temp_molecule_config)
    kv.sanity_checks()
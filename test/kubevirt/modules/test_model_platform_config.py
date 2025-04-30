import pytest
import yaml
import os

from molecule_plugins.kubevirt.modules.model.defaults import DefaultConfig
from molecule_plugins.kubevirt.modules.model.platform_config import PlatformConfig, \
    PlatformConfigList

# Define the path to the YAML directory
DATA_DIR = "data_fixture/platform_config/"

@pytest.fixture
def platform_data(request) -> list[dict]:
    """
    Loads platform data from a yml file, keeping our test file more compact
    but also testing parsing the platform data as yaml. Technically ansible/molecule
    handles that so we don't need to test it, but it's nice to validate no errors in
    our yaml setup
    """
    file_name = request.param  # The filename will be passed here indirectly
    file_path = os.path.join(DATA_DIR, file_name)

    # Load and parse YAML data
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    return data

@pytest.fixture
def default_config():
    return DefaultConfig()

@pytest.mark.parametrize(
    ("platform_data"),  # Corrected to tuple
    [
        ( "simple_1.yml" ),
        ( "simple_2.yml" ),
        ( "disk.yml" ),
        ( "interface.yml" ),
        ( "full_schema.yml" ),
    ],
    indirect=["platform_data"], # Load platform data from our fixture
    ids=["basic_config", "two_basic_config", "disk", "interface", "full_schema"],
)
def test_platform_config_load(platform_data, default_config):
    pcl = PlatformConfigList.from_dict(platform_data, default_config)
    assert isinstance(pcl, PlatformConfigList)
    assert all(isinstance(p, PlatformConfig) for p in pcl.platform_configs)
    assert len(pcl.platform_configs) == len(platform_data)

    for i, pd in enumerate(platform_data):
        pcli = pcl.platform_configs[i]
        assert pcli.name == pd["name"]
        assert pcli.cores == default_config.cores

        if "disks" in pd:
            assert len(pcli.disks) == len(pd["disks"])
            for k, disk in enumerate(pd["disks"]):
                if "size" in disk:
                    assert pcli.disks[k].size == disk["size"]
                else:
                    assert pcli.disks[k].size == default_config.disk_size
                if "accessMode" in disk:
                    assert pcli.disks[k].accessMode == disk["accessMode"]
                else:
                    assert pcli.disks[k].accessMode == default_config.disk_access_mode
        if "interfaces" in pd:
            assert len(pcli.interfaces) == len(pd["interfaces"])
            for k, iface in enumerate(pd["interfaces"]):
                assert pcli.interfaces[k].name == iface["name"]
                if "type" in iface:
                    assert pcli.interfaces[k].type == iface["type"]
                else:
                    assert pcli.interfaces[k].type == default_config.interface_type
        if "cloudInit" in pd:
            pass

@pytest.mark.parametrize(
    "platform_data, expected_failure",
    [
        ( "duplicate_name.yml", "duplicate name: testnode" ),
        ( "invalid_key.yml", "[PlatformConfig] Invalid key(s) found: cpus" ),
        ( "missing_name.yml", '[PlatformConfig] Missing required key(s): name' ),
        ( "disk_missing_name.yml", '[DiskConfig] Missing required key(s): name' ),
        ( "interface_missing_name.yml", '[InterfaceConfig] Missing required key(s): name' ),
        ( "missing_rootfsclass.yml", '[PlatformConfig] Missing required key(s): rootFsStorageClass' ),
    ],
    indirect=["platform_data"],
    ids=["duplicate_name", "invalid_key", "missing_name", "disk_missing_name",
         "interface_missing_name", "missing_rootfsclass"
    ],
)
def test_platform_config_load_failure(platform_data, expected_failure, default_config):
    with pytest.raises(Exception) as excinfo:
        PlatformConfigList.from_dict(platform_data, default_config)

    assert str(excinfo.value) == expected_failure
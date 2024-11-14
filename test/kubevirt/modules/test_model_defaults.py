import pytest
import yaml

from molecule_plugins.kubevirt.modules.model.defaults import DefaultConfig

def test_model_default_config_todict():
    """ Tests both the inborn defaults and that we can change defaults """
    defaults = DefaultConfig(cores=4)
    default_dict = defaults.to_dict()
    assert isinstance(default_dict, dict)
    assert default_dict["arch"] == "amd64"
    assert default_dict["cloud_init_type"] == "cloudInitNoCloud"
    assert default_dict["cores"] == 4
    assert default_dict["disk_access_mode"] == "ReadWriteMany"
    assert default_dict["disk_size"] == "10Gi"
    assert default_dict["disk_type"] == "virtio"
    assert default_dict["disk_volume_mode"] == "Block"
    assert default_dict["interface_name"] == "enp1s0"
    assert default_dict["interface_type"] == "virtio"
    assert default_dict["machine_type"] == "q35"
    assert default_dict["memory"] == "2Gi"
    assert default_dict["namespace"] == "default"
    assert default_dict["root_fs_name"] == "root-fs"
    assert default_dict["secure_boot"] == False
    assert default_dict["ssh_port"] == "22"
    assert default_dict["ssh_user"] == "ubuntu"
    assert default_dict["memory_ratio"] == 0.5
    assert default_dict["cpu_ratio"] == 0.5

def test_model_default_config_fromdict():
    """ Tests both the inborn defaults and that we can change defaults """
    default_dict = {
        "arch": "arm64",
    }
    defaults = DefaultConfig.from_dict(default_dict)
    assert defaults.cloud_init_type == "cloudInitNoCloud"
    assert defaults.cores == 2
    assert defaults.disk_access_mode == "ReadWriteMany"
    assert defaults.disk_size == "10Gi"
    assert defaults.disk_type == "virtio"
    assert defaults.disk_volume_mode == "Block"
    assert defaults.interface_name == "enp1s0"
    assert defaults.interface_type == "virtio"
    assert defaults.machine_type == "q35"
    assert defaults.memory == "2Gi"
    assert defaults.namespace == "default"
    assert defaults.root_fs_name == "root-fs"
    assert defaults.secure_boot == False
    assert defaults.ssh_port == "22"
    assert defaults.ssh_user == "ubuntu"
    assert defaults.memory_ratio == 0.5
    assert defaults.cpu_ratio == 0.5

def test_model_default_config_bad_value():
    """ Tests that we get an error if an unknown value is passed """
    default_dict = {
        "cpus": 5
    }
    with pytest.raises(TypeError) as te:
        defaults = DefaultConfig.from_dict(default_dict)
        assert str(te.value) == ("DefaultConfig.__init__() got an unexpected keyword "
                                 "argument 'cpus'")
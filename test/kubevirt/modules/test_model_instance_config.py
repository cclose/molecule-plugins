import pytest
import yaml

from molecule_plugins.kubevirt.modules.model.instance_config import InstanceConfig, InstanceConfigList


@pytest.fixture
def test_yaml():
    """Provide sample YAML data for testing."""
    return """
    - instance: node1
      address: 10.1.2.3
      user: ubuntu
      port: 22
      identity_file: "/Users/jdoe/.cache/molecule/rolename/default/id_ed25519"
      id: b10e1e72049e419dbdffddeee1537d1a
      uid: 3cee2a38-ac0c-5f0e-981d-7b8e4b6d8caa
      namespace: testing
      run_id: mics9
    - instance: node2
      address: 10.1.2.4
      user: ubuntu
      port: 22
      identity_file: "/Users/jdoe/.cache/molecule/rolename/default/id_ed25519"
      id: b20e1e72049e419dbdffddeee1537d2a
      uid: 4dee2a38-ac0c-5f0e-981d-7b8e4b6d8dba
      namespace: testing
      run_id: mics10
    - instance: node3
      address: 10.1.2.5
      user: ubuntu
      port: 22
      password: "secretSecureP4$$"
      id: b30e1e72049e419dbdffddeee1537d3a
      uid: 4dee2a38-ac0c-5f0e-981d-7b8e4b6d8dca
      namespace: testing
      run_id: mics10
    """

@pytest.fixture
def test_instance_config():
    """Provide a sample InstanceConfigList for testing."""
    # Manually create the InstanceConfig objects
    instance_config1 = InstanceConfig(
        instance="node1",
        address="10.1.2.3",
        user="ubuntu",
        port=22,
        identity_file="/Users/jdoe/.cache/molecule/rolename/default/id_ed25519",
        id="b10e1e72049e419dbdffddeee1537d1a",
        uid="3cee2a38-ac0c-5f0e-981d-7b8e4b6d8caa",
        namespace="testing",
        run_id="mics9"
    )

    instance_config2 = InstanceConfig(
        instance="node2",
        address="10.1.2.4",
        user="ubuntu",
        port=22,
        identity_file="/Users/jdoe/.cache/molecule/rolename/default/id_ed25519",
        id="b20e1e72049e419dbdffddeee1537d2a",
        uid="4dee2a38-ac0c-5f0e-981d-7b8e4b6d8dba",
        namespace="testing",
        run_id="mics10"
    )

    instance_config3 = InstanceConfig(
        instance="node3",
        address="10.1.2.5",
        user="ubuntu",
        port=22,
        password="secretSecureP4$$",
        id="b30e1e72049e419dbdffddeee1537d3a",
        uid="4dee2a38-ac0c-5f0e-981d-7b8e4b6d8dca",
        namespace="testing",
        run_id="mics10"
    )

    # Return an InstanceConfigList containing both InstanceConfig objects
    return InstanceConfigList([instance_config1, instance_config2, instance_config3])

@pytest.fixture
def test_instance_config2():
    """
    A second set of data to provide a negative test to make sure our tests
    are working
    """
    return InstanceConfigList([
        InstanceConfig(
            instance="vm1",
            address="10.2.2.5",
            user="root",
            port=9222,
            identity_file="/Users/bob/.cache/molecule/rolename/default/id_ed25519",
            uid="3cee2a38-ac0c-5f0e-231d-7b8edeadbeef",
            namespace="testing",
            run_id="bob12"
        )
    ])

def test_instance_config_list(test_instance_config):
    """Test that InstanceConfigList fixture returns correct data."""
    assert len(test_instance_config.instance_configs) == 3
    assert test_instance_config.instance_configs[0].instance == "node1"
    assert test_instance_config.instance_configs[1].run_id == "mics10"

def test_instance_config_parsing(test_yaml, test_instance_config, test_instance_config2):
    """Test parsing YAML to InstanceConfigList and vice versa."""
    # Load the YAML into an InstanceConfigList object
    instance_config_list_from_yaml = InstanceConfigList.from_yaml(test_yaml)

    # Validate that the parsed object matches the expected instance data
    assert instance_config_list_from_yaml == test_instance_config
    assert instance_config_list_from_yaml != test_instance_config2
    # Just to be extra certain our negative tests are working properly
    assert (instance_config_list_from_yaml.instance_configs[0]
            != test_instance_config2.instance_configs[0])

def test_instance_config_writing(test_instance_config, test_yaml):
    """Test dumping YAML"""
    yaml_from_ic = test_instance_config.to_yaml()

    try:
        # Try loading the YAML string back into a Python object to ensure it's valid YAML
        loaded_yaml = yaml.safe_load(yaml_from_ic)
    except yaml.YAMLError as e:
        pytest.fail(f"YAML parsing error occurred: {e}")


    # this is kind of Kludgey...
    ic_from_yaml = InstanceConfigList.from_yaml(yaml_from_ic)

    assert test_instance_config == ic_from_yaml

def test_instance_config_generate_dns_name():
    # Regular case: lowercase and replace invalid characters
    assert InstanceConfig.generate_dns_name("Test Name!") == "test-name"

    # Edge case: Uppercase letters are converted to lowercase
    assert InstanceConfig.generate_dns_name("TESTNAME") == "testname"

    # Edge case: Special characters are replaced with '-'
    assert InstanceConfig.generate_dns_name("Test@Name!") == "test-name"

    # Edge case: Leading and trailing dashes are stripped
    assert InstanceConfig.generate_dns_name("-Test-Name-") == "test-name"

    # Edge case: String with only invalid characters should become empty string
    assert InstanceConfig.generate_dns_name("****") == ""


@pytest.mark.parametrize(
    "dns_name, expected_k8s_name",
    [
        # Case where no truncation is needed (run_name is short)
        ("testname",
         "testname-run123"),

        # Case where truncation is needed (run_name is long)
        ("this-is-an-extremely-long-dns-name-bigger-than-k8s-len-and-needs-truncation",
         "this-is-an-extremely-long-dns-name-bigger-than-k8-run123-pod123"),

        # Case where the truncation of the DNS name is correct
        ("this-dns-name-isnt-too-long-but-it-will-be-when-we-add-run-id",
         "this-dns-name-isnt-too-long-but-it-will-be-when-w-run123-pod123")
    ],
    ids = [
        "no_truncation_short_run_name",
        "truncation_needed_long_run_name",
        "dns_name_truncation"
    ]
)
def test_instance_config_generate_k8s_name(dns_name, expected_k8s_name):
    run_id = "run123"
    pod_id = "pod123"
    run_name = f"{dns_name}-{run_id}"

    k8s_name = InstanceConfig.generate_k8s_name(dns_name, run_id, pod_id, run_name)
    assert k8s_name == expected_k8s_name

@pytest.mark.parametrize(
    "dns_name, sub_name, expected_k8s_name",
    [
        # Case where no truncation is needed (run_name is short)
        ("testname",
         "data-disk",
         "testname-data-disk-run123"),

        ("testname",
         "data_disk",
         "testname-data-disk-run123"),

        # Case where truncation is needed (run_name is long)
        ("this-is-an-extremely-long-dns-name-bigger-than-k8s-len-and-needs-truncation",
         "data-disk",
         "this-is-an-extremely-long-dns-name-bigg-data-disk-run123-pod123"),

        # Case where the truncation of the DNS name is correct
        ("this-dns-name-isnt-too-long-but-it-will-be-when-we-add-run-id",
         "data-disk",
         "this-dns-name-isnt-too-long-but-it-will-data-disk-run123-pod123"),

        ("testname-node1",
         "super-duper-mega-awesome-mighty-morphin-data-diskin-rangers",
         "testna-super-duper-mega-awesome-mighty-morphin-da-run123-pod123"),
    ],
    ids = [
        "no_truncation_short_run_name",
        "truncation_needed_long_run_name",
        "dns_name_truncation",
        "sub_name_dns_unsafe",
        "sub_name_too_long",
    ]
)
def test_instance_config_generate_k8s_subresource_name(dns_name, sub_name, expected_k8s_name):
    run_id = "run123"
    pod_id = "pod123"

    k8s_name = InstanceConfig.generate_k8s_subresource_name(sub_name, dns_name, run_id, pod_id)
    assert k8s_name == expected_k8s_name


def test_instance_config_generate_instance_id():
    instance_id = InstanceConfig.generate_instance_id()
    assert all(c in '0123456789abcdef' for c in instance_id)  # It should be a hex string

def test_instance_config_dns_name_property():
    instance = "Test Instance"
    obj = InstanceConfig(instance=instance, run_id="run123")
    assert obj.dns_name == "test-instance"  # Ensure it uses the DNS-safe name

def test_instance_config_run_name_property():
    instance = "Test Instance"
    obj = InstanceConfig(instance=instance, run_id="run123")
    assert obj.run_name == "test-instance-run123"  # Ensure it uses the DNS-safe name

def test_instance_config_pod_id_property():
    obj = InstanceConfig(instance="test-instance", run_id="run123", id="1234567890abcdef")
    assert len(obj.pod_id) == InstanceConfig._POD_ID_LEN  # The length should be exactly 6
    assert obj.pod_id == "123456"  # Only the first 6 characters should be used

def test_instance_config_pod_name_property():
    obj = InstanceConfig(instance="test-instance", run_id="run123")
    assert obj.pod_name == "test-instance-run123"  # Ensure it generates the k8s name correctly

def test_instance_config_molecule_id_property():
    obj = InstanceConfig(instance="test-instance", run_id="run123", id="1234567890abcdef")
    assert obj.molecule_id == "run123_1234567890abcdef"  # Only the first 6 characters should be used

def test_instance_config_get_subresource_name():
    obj = InstanceConfig(instance="test-instance", run_id="run123", id="1234567890abcdef")
    assert obj.get_subresource_name('data') == "test-instance-data-run123"


@pytest.mark.parametrize(
    "key, value, expected_failure",
    [
        ("dns_name", "bad_dns", "Sanity check failed: provided 'dns_name' (bad_dns) does not match calculated"
          + "'dns_name' (test-instance)."
         ),

        ("pod_name", "pod-pod-pod",
            "Sanity check failed: provided 'pod_name' (pod-pod-pod) does not match calculated 'pod_name' "
            "(test-instance-run123)."
         ),

        ("pod_id", "pod567",
            "Sanity check failed: provided 'pod_id' (pod567) does not match calculated 'pod_id' " "(pod567)."
         ),

        ("run_name", "run-spot-run",
            "Sanity check failed: provided 'run_name' (run-spot-run) does not match calculated 'run_name' "
            "(test-instance-run123)."
         ),

    ],
    ids = [
        "dns_name", "pod_name", "pod_id", "run_name",
    ]
)
def test_instance_config_from_dict_sanity_checks(key, value, expected_failure):
    test_dict = {'instance': 'test-instance', 'address': 'test-instance.devlab.local', 'port': 22, 'user': 'ubuntu',
                 'identity_file': '/path/to/file', 'uid': '4dee2a38-ac0c-5f0e-981d-7b8e4b6d8dca', 'run_id': 'run123',
                 'id': 'b30e1e72049e419dbdffddeee1537d3a', 'namespace': 'testing', key: value}

    with pytest.raises(ValueError) as e:
        InstanceConfig.from_dict(test_dict)
        assert str(e.value) == expected_failure


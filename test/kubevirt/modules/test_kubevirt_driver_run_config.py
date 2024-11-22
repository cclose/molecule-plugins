import textwrap

import pytest
from unittest.mock import patch, MagicMock

import yaml
from ansible.module_utils.basic import AnsibleModule

import molecule_plugins.kubevirt.modules.model.run_config
from molecule_plugins.kubevirt.modules.kubevirt_driver_run_config import main
from .helpers import patch_exit_fail_json


# Mock module name for readability
module_name = "molecule_plugins.kubevirt.modules.kubevirt_driver_run_config"

@pytest.fixture
def mock_ansible_module():
    """Fixture to mock AnsibleModule with parameters."""
    with patch(f"{module_name}.AnsibleModule") as MockModule:
        mock_module = MockModule.return_value
        yield from patch_exit_fail_json(mock_module)


run_config_obj = "molecule_plugins.kubevirt.modules.model.run_config.RunConfig"

@pytest.fixture
def mock_data(request):
    """
    Centralized fixture to provide YAML data and expected results for each test case.
    """
    return {
        "simple": {
            "yml": textwrap.dedent("""
                run_id: 0tjo7
                run_prefix: m-scenarios-default-
                molecule_project: scenarios
                scenario_name: default
            """),
            "expected": {
                "run_id": "0tjo7",
                "run_prefix": "m-scenarios-default-",
                "molecule_project": "scenarios",
                "scenario_name": "default",
            },
        },
        "simple-full": {
            "yml": textwrap.dedent("""
                run_id: 0tjo7
                run_prefix: m-scenarios-default-
                molecule_project: scenarios
                molecule_app_label: m-scenarios-default--0tjo7
                scenario_name: default
                ssh_key_path: null
                ssh_key_token: SSH_PUBLIC_KEY
                ssh_public_key: null
            """),
            "expected": {
                "run_id": "0tjo7",
                "run_prefix": "m-scenarios-default-",
                "molecule_project": "scenarios",
                "molecule_app_label": "m-scenarios-default--0tjo7",
                "scenario_name": "default",
                "ssh_key_path": "null",
                "ssh_key_token": "SSH_PUBLIC_KEY",
                "ssh_public_key": "null",
            },
        },
        "valid": {
            "yml": textwrap.dedent("""
                run_id: 0tjo7
                run_prefix: m-scenarios-default-
                molecule_project: scenarios
                molecule_app_label: m-scenarios-default--0tjo7
                scenario_name: default
                ssh_key_path: /Users/CoryClose/.cache/molecule/scenarios/default/id_ed25512_ll5ar
                ssh_key_token: SSH_PUBLIC_KEY
                ssh_public_key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOYQGAJrzUK6CHhbGm6pMu2qiV7XL8B4Ky+ry9N9LtYg
            """),
            "expected": {
                "run_id": "0tjo7",
                "run_prefix": "m-scenarios-default-",
                "molecule_project": "scenarios",
                "molecule_app_label": "m-scenarios-default--0tjo7",
                "scenario_name": "default",
                "ssh_key_path": "/Users/CoryClose/.cache/molecule/scenarios/default/id_ed25512_ll5ar",
                "ssh_key_token": "SSH_PUBLIC_KEY",
                "ssh_public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOYQGAJrzUK6CHhbGm6pMu2qiV7XL8B4Ky+ry9N9LtYg",
            },
        },
        "empty": {
            "yml": "",
            "expected": {},  # Empty file case
        },
    }

@pytest.fixture
def rc_file(tmp_path, request, mock_data):
    """
    Fixture to create a temporary YAML file for the specified test case.
    """
    case = request.param
    data = mock_data.get(case, {})
    yml_content = data.get("yml", "")

    temp_file = tmp_path / "run_config.yml"
    if yml_content:  # Write only if content is provided
        temp_file.write_text(yml_content.strip())

    return temp_file

@pytest.fixture
def expected_results(request, mock_data):
    """
    Fixture to fetch expected results for the specified test case.
    """
    changed, yaml_case, data_case, msg = request.param
    data = mock_data.get(data_case, None)
    er = {
        "changed": changed,
    }

    if yaml_case is not None:
        er['run_yml'] = mock_data[yaml_case]['yml'].strip('\n')
        er['run_yml']

    if data_case is not None:
        er['run_config'] = mock_data[data_case]['expected']

    if msg is not None:
        er['msg'] = msg

    return er

@pytest.fixture
def rc_data(request, mock_data):
    case_name = request.param
    return mock_data[case_name]["expected"]

@pytest.fixture
def mock_getenv():
    mock_env = {
        "MOLECULE_SCENARIO_NAME": "test-scenario",
        "MOLECULE_PROJECT_DIRECTORY": "/path/to/test-project"
    }

    # Mock os.getenv to return values from mock_env
    with patch("os.getenv", side_effect=lambda key, default=None: mock_env.get(key, default)) as mock_get_env:
        yield mock_get_env

@pytest.mark.parametrize(
    "action, check_mode, raises, rc_file, rc_data, expected_results",
    [
        # Test: "load" action with file found
        ("load", False, False, 'valid', 'empty', (True, 'valid', 'valid', None) ),
        # Test: "load" action with file not found
        ("load", False, False, 'empty', 'empty', (False, 'empty', 'empty',  "run_config file not found, initialized blank") ),
        # Test: "save" action (check_mode=False)
        ("save", True, False, 'empty', 'simple', (True, 'simple-full', None, "Check Mode: would have written" )),
        ("save", False, False, 'empty', 'simple', (True, 'simple-full', None, None )),
        ("save", False, True, 'empty', 'empty', (False, None, None, "'run_config' is required when 'action' is 'save'" )),
        # Test: "save" action (check_mode=True)
    ],
    indirect=["rc_file", "rc_data", "expected_results"],
)
def test_kubevirt_driver_run_config(mock_ansible_module, mock_getenv, action, check_mode, raises, rc_file, rc_data, expected_results):
    """
    Test the kubevirt_driver_wait_for_lease module with various scenarios, including successful IP lease retrieval,
    timeout errors, and missing VMI errors.
    """
    mock_module, mock_exit_json, mock_fail_json = mock_ansible_module
    params = {
        "action": action,
        "path": rc_file,
    }
    if rc_data is not None and rc_data != {}:
        params["run_config"] = rc_data
    mock_module.params = params
    mock_module.check_mode = check_mode

    with pytest.raises(SystemExit) as e:
        main()  # assuming main() handles the action logic

    cargs = None
    ckwargs = None

    exit_data = {
        'exit_json': mock_exit_json.call_count,
        'exit_json_args': mock_exit_json.call_args_list,
        'fail_json': mock_fail_json.call_count,
        'fail_json_args': mock_fail_json.call_args_list,
    }

    try:
        if raises:
            mock_fail_json.assert_called_once()
            cargs, ckwargs = mock_fail_json.call_args
        else:
            mock_exit_json.assert_called_once()
            cargs, ckwargs = mock_exit_json.call_args
    except AssertionError as e:
        raise AssertionError(f"Failed exit assertion: \n{exit_data}\ne: {e}")

    if expected_results.get("msg", ""):
        assert ckwargs.get("msg", "").startswith(expected_results["msg"])

    if expected_results.get("changed", False):
        assert expected_results["changed"] == ckwargs["changed"]

    if expected_results.get("run_yml", ""):
        assert yaml.safe_load(expected_results["run_yml"]) == yaml.safe_load(ckwargs["run_yml"])

    if expected_results.get("run_config", ""):
        assert expected_results["run_config"] == ckwargs["run_config"]
import pytest
from typing import Final
from unittest.mock import patch, MagicMock
from ansible.module_utils.basic import AnsibleModule
from molecule_plugins.kubevirt.modules.kubevirt_driver_process_instance_data import main

from .helpers import patch_exit_fail_json

# Alias module name to a 'const' because it's so darn long
module_name : Final[str] = "molecule_plugins.kubevirt.modules.kubevirt_driver_process_instance_data" # noqa: ES501

@pytest.fixture
def mock_ansible_module(action):
    with (patch(f"{module_name}.AnsibleModule") as MockModule):
        mock_module = MockModule.return_value
        mock_module.params = {
            'action': action,
            'instance_config': [], #{'name': 'instance1', 'type': 'vm'}],
            'platform_config': [{'name': 'instance1', 'rootFsStorageClass': 'harvester-dv-001'}],
            'run_config': {'run_id': 'test01'},
        }

        yield from patch_exit_fail_json(mock_module)

# Parametrized test to handle different actions
@pytest.mark.parametrize("action, expect_fail, expected_result", [
    ('prepare', False, {"changed": False}),
    ('parse_drive', False, {"changed": False}),
    ('invalid_action', True, {"msg": "Unexpected error: Invalid `action` parameter: invalid_action"}),
])
def test_kubevirt_driver_process_instance_data_actions(mock_ansible_module, action, expect_fail, expected_result):
    """Test the main function with different actions and verify expected results."""
    # Get the mock objects from the fixture
    mock_module, mock_exit_json, mock_fail_json = mock_ansible_module

    # Update the action in the mock
    mock_module.params['action'] = action

    with pytest.raises(SystemExit) as e:
        result = main()  # assuming main() handles the action logic
        assert result == expected_result

    cargs = None
    ckwargs = None
    if expect_fail:
        mock_fail_json.assert_called_once()
        cargs, ckwargs = mock_fail_json.call_args
    else:
        mock_exit_json.assert_called_once()
        cargs, ckwargs = mock_exit_json.call_args

    assert ckwargs == expected_result

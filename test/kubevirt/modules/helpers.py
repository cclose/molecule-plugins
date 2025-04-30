import pytest
from unittest.mock import patch, MagicMock
from ansible.module_utils.basic import AnsibleModule

EXIT_JSON_PATH = "ansible.module_utils.basic.exit_json"
FAIL_JSON_PATH = "ansible.module_utils.basic.fail_json"

def patch_exit_fail_json(mock_module):
    # Mock exit_json and fail_json but simulate a sys.exit() call
    with patch.object(mock_module, "exit_json") as mock_exit_json, patch.object(mock_module, "fail_json") as mock_fail_json: # noqa: ES501
        mock_exit_json.side_effect = SystemExit("Exit called")
        mock_fail_json.side_effect = SystemExit("Fail called")

        # Attach the mock functions to the mock module
        mock_module.exit_json = mock_exit_json
        mock_module.fail_json = mock_fail_json

        yield mock_module, mock_exit_json, mock_fail_json

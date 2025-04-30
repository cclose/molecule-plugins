import pytest
from unittest.mock import patch, MagicMock
from ansible.module_utils.basic import AnsibleModule
from molecule_plugins.kubevirt.modules.kubevirt_driver_wait_for_lease import main
from .helpers import patch_exit_fail_json


# Mock module name for readability
module_name = "molecule_plugins.kubevirt.modules.kubevirt_driver_wait_for_lease"

@pytest.fixture
def mock_ansible_module():
    """Fixture to mock AnsibleModule with parameters."""
    with patch(f"{module_name}.AnsibleModule") as MockModule:
        mock_module = MockModule.return_value
        yield from patch_exit_fail_json(mock_module)


@pytest.fixture
def mock_kube_util():
    """Fixture to mock the kube_util helper function."""
    with patch(f"molecule_plugins.kubevirt.modules.util.kube.get_vmi_ip") as mock_get_vmi_ip:
        yield mock_get_vmi_ip


@pytest.mark.parametrize(
    "params, mock_return_value, raises_error, expected_result",
    [
        (
            # Test case: Successful IP lease retrieval
            {
                "kubeconfig": "/path/to/kubeconfig",
                "name": "test-vmi",
                "namespace": "default",
                "wait_for_lease": True,
                "retries": 5,
                "timeout": 15,
            },
            "192.168.1.20",  # Mock IP to return
            None,  # No error raised
            {
                "changed": False,
                "ip": "192.168.1.20",
                "msg": "Retrieved IP",
            },
        ),
        (
            # Test case: TimeoutError raised by kube_util (simulate failure on lease retrieval)
            {
                "kubeconfig": "/path/to/kubeconfig",
                "name": "test-vmi",
                "namespace": "default",
                "wait_for_lease": True,
                "retries": 5,
                "timeout": 15,
            },
            None,
            TimeoutError("Timeout waiting for lease"),
            {'msg': 'Timeout waiting for lease: Timeout waiting for lease'}
        ),
        (
            # Test case: ValueError raised by kube_util (simulate missing VMI details)
            {
                "kubeconfig": "/path/to/kubeconfig",
                "name": "test-vmi",
                "namespace": "default",
                "wait_for_lease": False,
                "retries": 6,
                "timeout": 10,
            },
            None,
            ValueError("Failed to find pod: Failed to find VMI"),
            {'msg': 'Failed to find pod: Failed to find pod: Failed to find VMI'}
        ),
    ],
)
def test_kubevirt_driver_wait_for_lease(mock_ansible_module, mock_kube_util, params, mock_return_value, raises_error, expected_result):
    """
    Test the kubevirt_driver_wait_for_lease module with various scenarios, including successful IP lease retrieval,
    timeout errors, and missing VMI errors.
    """
    mock_module, mock_exit_json, mock_fail_json = mock_ansible_module
    mock_module.params = params

    if raises_error:
        mock_kube_util.side_effect = raises_error
    else:
        mock_kube_util.return_value = mock_return_value

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
        if raises_error:
            mock_fail_json.assert_called_once()
            cargs, ckwargs = mock_fail_json.call_args
        else:
            mock_exit_json.assert_called_once()
            cargs, ckwargs = mock_exit_json.call_args
    except AssertionError as e:
        raise AssertionError(f"Failed exit assertion: \n{exit_data}\ne: {e}")

    assert ckwargs == expected_result
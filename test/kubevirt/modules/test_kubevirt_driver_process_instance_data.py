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
    instance_config = [
        {
            'instance': 'instance1',
            'address': '',
            'user': 'ubuntu',
            'port': 22,
            'identity_file': '',
            'namespace': 'default',
            'id': 'c29a9dcff9b54f5b961e35fc3b2e2582',
            'run_id': 'test01',
            'uid': '',
        },
    ]
    with (patch(f"{module_name}.AnsibleModule") as MockModule):
        mock_module = MockModule.return_value
        params = {
            'action': action,
            'instance_config': instance_config,
        }
        if action == 'prepare':
            params['platform_config'] = [{'name': 'instance1', 'rootFsStorageClass': 'harvester-dv-001'}]
            params['run_config'] = {'run_id': 'test01'}
            params['default_config'] = None
        elif action == 'parse_instance':
            params['instance_data'] = [
                {
                    'result': {
                        'metadata': {
                            'uid': 'abc12345678edf',
                            'labels': {
                                'molecule_id': 'test01_c29a9dcff9b54f5b961e35fc3b2e2582'
                            }
                        }
                    }
                }
            ]

        mock_module.params = params

        yield from patch_exit_fail_json(mock_module)

@pytest.fixture
def results(request):
    case = request.param
    cases = {
    "default": {
        'changed': True,
        'instance_data': [
            {
                'arch': 'amd64',
                'cores': 2,
                'cpuRatio': 0.5,
                'cpuRequests': 1.0,
                'disks': [{'disk': {'bus': 'virtio'}, 'name': 'rootfs'}],
                'dns_safe_name': 'instance1',
                'interfaces': [{'bridge': {},
                                'model': 'virtio',
                                'name': 'enp1s0'}],
                'machineType': 'q35',
                'memory': '2Gi',
                'memoryRatio': 0.5,
                'memoryRequests': '1 GB',
                'molecule_id': 'test01_c29a9dcff9b54f5b961e35fc3b2e2582',
                'name': 'instance1',
                'namespace': 'default',
                'networks': [{'multus': None, 'name': 'enp1s0'}],
                'pod_name': 'instance1-test01',
                'pvcs': [{'accessMode': 'ReadWriteMany',
                          'diskName': 'rootfs',
                          'name': 'instance1-rootfs-test01',
                          'size': '10Gi',
                          'storageClass': 'harvester-dv-001',
                          'volumeMode': 'Block'}],
                'run_name': 'instance1-test01',
                'secureBoot': False,
                'volumes': [{'name': 'rootfs',
                             'persistentVolumeClaim': {'claimName': 'instance1-rootfs-test01'}}]}],
         'msg': 'Instance Data Prepared'},
        "invalid_action": {"msg": "Unexpected error: Invalid `action` parameter: invalid_action"},
        "no_change": { "changed": False},
        "ic_updated": {
            'changed': True,
            'instance_config': [
                {
                    'address': '',
                    'dns_name': 'instance1',
                    'id': 'c29a9dcff9b54f5b961e35fc3b2e2582',
                    'identity_file': '',
                    'instance': 'instance1',
                    'password': None,
                    'pod_id': 'c29a9d',
                    'pod_name': 'instance1-test01',
                    'port': 22,
                    'run_id': 'test01',
                    'uid': 'abc12345678edf',
                    'user': 'ubuntu',
                },
            ],
            'msg': 'Instance Config Updated from results',
        }
    }

    return cases[case]

# Parametrized test to handle different actions
@pytest.mark.parametrize(
    "action, expect_fail, results", [
        ('prepare', False, "default"),
        ('parse_instance', False, "ic_updated"),
        ('invalid_action', True, "invalid_action"),
    ],
    indirect=["results"],
)
def test_kubevirt_driver_process_instance_data_actions(mock_ansible_module, action, expect_fail, results):
    """Test the main function with different actions and verify expected results."""
    # Get the mock objects from the fixture
    mock_module, mock_exit_json, mock_fail_json = mock_ansible_module

    # Update the action in the mock
    mock_module.params['action'] = action

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
        if expect_fail:
            mock_fail_json.assert_called_once()
            cargs, ckwargs = mock_fail_json.call_args
        else:
                mock_exit_json.assert_called_once()
                cargs, ckwargs = mock_exit_json.call_args
    except AssertionError as e:
        raise AssertionError(f"Failed exit assertion: \n{exit_data}\ne: {e}")

    assert ckwargs == results

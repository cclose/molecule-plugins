import unittest
from unittest.mock import patch, MagicMock

from kubernetes.client import ApiException

from molecule_plugins.kubevirt.modules.util.kube import get_vmi_ip

class TestGetVmiIp(unittest.TestCase):
    @patch('molecule_plugins.kubevirt.modules.util.kube.client.CustomObjectsApi')  # Mock Kubernetes API
    @patch('molecule_plugins.kubevirt.modules.util.kube.config.load_kube_config')  # Mock kubeconfig loading
    def test_get_vmi_ip(self, mock_load_kube_config, mock_api_client):
        """Test that the IP is correctly retrieved."""
        # Mock the API response
        mock_api = mock_api_client.return_value
        mock_api.get_namespaced_custom_object.return_value = {
            'status': {
                'interfaces': [{'ipAddress': '192.168.1.10'}]
            }
        }

        ip = get_vmi_ip(
            instance_pod_name="test-vmi",
            namespace="default",
            kubeconfig_path="kubeconfig.yml"
        )
        self.assertEqual(ip, '192.168.1.10')
        mock_api.get_namespaced_custom_object.assert_called_once()

    @patch('molecule_plugins.kubevirt.modules.util.kube.client.CustomObjectsApi')
    @patch('molecule_plugins.kubevirt.modules.util.kube.config.load_kube_config')
    @patch('time.sleep')
    def test_get_vmi_ip_retry_logic(self, mock_sleep, mock_load_kube_config, mock_api_client):
        """Test retry logic when the IP is initially missing."""
        # Mock the API response: No IP on first call, IP on second call
        mock_api = mock_api_client.return_value
        mock_api.get_namespaced_custom_object.side_effect = [
            ApiException(status=404, reason='not found'),
            {'status': {'interfaces': [{}]}},  # No IP on first call
            {'status': {'interfaces': [{'ipAddress': '192.168.1.20'}]}},  # IP on second call
        ]

        ip = get_vmi_ip(
            instance_pod_name="test-vmi",
            namespace="default",
            kubeconfig_path="kubeconfig.yml",
            wait_for_lease=True,
            wait_timeout=1,
            wait_retries=2
        )
        self.assertEqual(ip, '192.168.1.20')
        self.assertEqual(3, mock_api.get_namespaced_custom_object.call_count)
        self.assertEqual(2, mock_sleep.call_count)

    @patch('molecule_plugins.kubevirt.modules.util.kube.client.CustomObjectsApi')
    @patch('molecule_plugins.kubevirt.modules.util.kube.config.load_kube_config')
    @patch('time.sleep')
    def test_get_vmi_ip_timeout_error(self, mock_sleep, mock_load_kube_config, mock_api_client):
        """Test timeout when IP is never available."""
        # Mock the API response: No IP on all calls
        mock_api = mock_api_client.return_value
        mock_api.get_namespaced_custom_object.return_value = {'status': {'interfaces': [{}]}}

        with self.assertRaises(TimeoutError):
            get_vmi_ip(
                instance_pod_name="test-vmi",
                namespace="default",
                kubeconfig_path="kubeconfig.yml",
                wait_for_lease=True,
                wait_timeout=1,
                wait_retries=3
            )
        self.assertEqual(mock_api.get_namespaced_custom_object.call_count, 4)  # Initial call + 3 retries

    @patch('molecule_plugins.kubevirt.modules.util.kube.client.CustomObjectsApi')
    @patch('molecule_plugins.kubevirt.modules.util.kube.config.load_kube_config')
    def test_get_vmi_ip_missing_parameters(self, mock_load_kube_config, mock_api_client):
        """Test ValueError is raised when parameters are missing."""
        with self.assertRaises(ValueError):
            get_vmi_ip(instance_pod_name=None, namespace="default",
                       kubeconfig_path = "kubeconfig.yml")
        with self.assertRaises(ValueError):
            get_vmi_ip(instance_pod_name="test-vmi", namespace=None,
                       kubeconfig_path="kubeconfig.yml")


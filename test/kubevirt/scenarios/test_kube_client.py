from kubernetes import client, config
from kubernetes.client.rest import ApiException

kubeconfig="../../../src/molecule_plugins/kubevirt/playbooks/harvester.yaml"
namespace="harvester-public"
pod="default-5i0ju"
config.load_kube_config(config_file=kubeconfig)

vmi_client = client.CustomObjectsApi()

vmi = vmi_client.get_namespaced_custom_object(
    group="kubevirt.io",  # The group for KubeVirt CRDs
    version="v1",         # API version for VMI
    namespace=namespace,
    plural="virtualmachineinstances",  # Plural for VirtualMachineInstance
    name=pod
)

vmi_ip = vmi['status'].get('interfaces', [{}])[0].get('ipAddress', None)

print(f"IP: {vmi_ip}")



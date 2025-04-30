from ansible.module_utils.basic import AnsibleModule
import molecule_plugins.kubevirt.modules.util.kube as kube_util

DOCUMENTATION = """
---
module: get_vmi_ip
short_description: Retrieve the IP address of a KubeVirt VirtualMachineInstance (VMI)
description:
    - This module allows you to retrieve the IP address of a VirtualMachineInstance (VMI) deployed in a KubeVirt environment. 
    - It interacts with Kubernetes API to fetch the VMI's details, optionally retrying on failure until the IP is allocated.
    - Supports retry logic with configurable timeout and number of retries.
author:
    - Cory Close (@cclose)
version_added: "2.10"
requirements:
    - python >= 3.6
    - kubernetes >= 11.0.0
    - kubevirt >= 0.0.1
options:
    kubeconfig:
        description:
            - Path to the kubeconfig file to interact with the Kubernetes cluster. If not provided, the in-cluster configuration is used.
        type: str
        required: true
    name:
        description:
            - The name of the VirtualMachineInstance (VMI) whose IP is to be retrieved.
        type: str
        required: true
    namespace:
        description:
            - The Kubernetes namespace where the VMI is located.
        type: str
        required: true
    wait_for_lease:
        description:
            - Whether to wait for the VMI's IP to be allocated before returning. Defaults to false.
        type: bool
        default: false
    retries:
        description:
            - The number of retries to attempt if the VMI's IP address is not immediately available. Defaults to 6.
        type: int
        required: false
        default: 6
    timeout:
        description:
            - Timeout in seconds to wait for the IP address to be allocated. Defaults to 10.
        type: int
        required: false
        default: 10
supports_check_mode: true
notes:
    - In check mode, no changes are made, but the module will simulate the changes and set the "changed" status accordingly.
"""

EXAMPLES = """
- name: Retrieve VMI IP address
  get_vmi_ip:
    kubeconfig: "/path/to/kubeconfig"
    name: "test-vmi"
    namespace: "default"
    wait_for_lease: true
    retries: 5
    timeout: 15
  register: vmi_ip_result

- name: Show the retrieved VMI IP address
  debug:
    msg: "The IP address of the VMI is {{ vmi_ip_result.ip }}"
"""

RETURN = """
ip:
    description: The IP address of the VirtualMachineInstance (VMI).
    type: str
    returned: when the IP address is successfully retrieved.
    sample: "192.168.1.20"
changed:
    description: Indicates whether the operation has changed any state.
    type: bool
    returned: always
msg:
    description: A message indicating the result of the action (e.g., success, failure, check mode).
    type: str
    returned: always
"""

def main():
    """
    Main function for the custom Ansible module that retrieves the IP address of a VirtualMachineInstance (VMI)
    in a Kubernetes cluster using KubeVirt.

    It interacts with the KubeVirt Custom Resource Definitions (CRDs) to retrieve the VMI details.
    It includes retry and timeout options for waiting for the VMI IP address to become available.

    Returns:
        dict: A result dictionary that contains either the retrieved IP or an error message.
    """

    module = AnsibleModule(
        argument_spec=dict(
            kubeconfig=dict(type='str', required=True),
            name=dict(type='str', required=True),
            namespace=dict(type='str', required=True),
            wait_for_lease=dict(type='bool', default=False),
            retries=dict(type='int', required=False, default=6),
            timeout=dict(type='int', required=False, default=10),
        ),
        supports_check_mode=True
    )

    result = dict(
        changed=False,
    )

    try:
        # Call the helper function to get the IP address of the VirtualMachineInstance (VMI)
        ip = kube_util.get_vmi_ip(module.params.get("name"),
                                  namespace=module.params.get("namespace"),
                                  kubeconfig_path=module.params.get("kubeconfig"),
                                  wait_for_lease=module.params.get("wait_for_lease"),
                                  wait_timeout=module.params.get("timeout"),
                                  wait_retries=module.params.get("retries")
                                  )

        # If successful, return the IP address in the result
        result["ip"] = ip
        result["msg"] = "Retrieved IP"

    except TimeoutError as e:
        # Handle TimeoutError for lease waiting and return failure
        module.fail_json(msg=str(f"Timeout waiting for lease: {e}"))
    except ValueError as e:
        # Handle ValueError for missing VMI details (e.g., IP not found)
        module.fail_json(msg=str(f"Failed to find pod: {e}"))

    # Return the result (either success or failure)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

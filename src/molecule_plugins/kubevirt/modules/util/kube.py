from kubernetes import client, config
import time

from kubernetes.client import ApiException


def get_vmi_ip(instance_pod_name, namespace="default", kubeconfig_path=None,
               wait_for_lease=False, wait_timeout=10, wait_retries=6):
    """
    Retrieve the IP address of a VirtualMachineInstance (VMI), with optional retry logic.

    Args:
        instance_pod_name (str): The name of the pod instance.
        namespace (str): The Kubernetes namespace of the VMI. Defaults to "default".
        kubeconfig_path (str, optional): Path to the kubeconfig file. Defaults to None
            (uses in-cluster configuration).
        wait_for_lease (bool): If True, retries fetching the VMI IP until it becomes available.
        wait_timeout (int): Time (in seconds) to wait between retries. Defaults to 10 seconds.
        wait_retries (int): Maximum number of retries before giving up. Defaults to 6.

    Returns:
        str: The IP address of the VMI.

    Raises:
        ValueError: If the namespace, pod name, or IP address is missing.
        TimeoutError: If the VMI IP is not available within the retry limit.
    """
    # Load the kubeconfig if provided, or default to in-cluster configuration
    if kubeconfig_path:
        config.load_kube_config(kubeconfig_path)
    else:
        config.load_incluster_config()

    if not namespace or not instance_pod_name:
        raise ValueError(f"Namespace ({namespace}) or Pod Name ({instance_pod_name}) is missing.")

    # Kubernetes API interaction
    vmi_client = client.CustomObjectsApi()

    attempts = 0
    while attempts <= wait_retries:
        try:
            vmi = vmi_client.get_namespaced_custom_object(
                group="kubevirt.io",
                version="v1",
                namespace=namespace,
                plural="virtualmachineinstances",
                name=instance_pod_name
            )

            # Extract IP
            vmi_ip = vmi['status'].get('interfaces', [{}])[0].get('ipAddress', None)

            #e.status == 404
            if vmi_ip:
                return vmi_ip  # IP successfully retrieved

            if not wait_for_lease:
                raise ValueError(f"VMI IP not found for {instance_pod_name} in namespace {namespace}")

        except ApiException as e:
            if e.status == 404 and not wait_for_lease:
                raise e  # Re-raise exception if retries are disabled

        # Retry logic
        attempts += 1
        if attempts > wait_retries:
            break

        time.sleep(wait_timeout)

    # Raise a timeout error after exhausting retries
    raise TimeoutError(
        f"Failed to retrieve VMI IP for {instance_pod_name} in namespace {namespace} "
        f"after {wait_retries} retries (wait_timeout={wait_timeout}s each)."
    )
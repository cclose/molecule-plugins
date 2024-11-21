#  Copyright (c) 2015-2018 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
"""KubeVirt Driver Module."""


import os
import warnings
from os.path import basename
from shutil import which

from ansible_compat.runtime import Runtime
from packaging.version import Version

from molecule import logger, util
from molecule.api import Driver, MoleculeRuntimeWarning
from molecule.constants import RC_SETUP_ERROR
from molecule.util import sysexit_with_message

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from molecule_plugins.kubevirt.modules.util.kube import get_vmi_ip

log = logger.get_logger(__name__)


class KubeVirt(Driver):
    """
    The class responsible for managing `KubeVirt`_ based testing infrastructure
    `KubeVirt`_ is `not` the default driver used in Molecule.

    Molecule uses the kubernetes.core.k8s ansible module while mapping
    variables from ``molecule.yml`` into ``create.yml`` and ``destroy.yml``.

    .. important::

    This driver is alpha quality software.  Do not perform any additional
    tasks inside the ``create`` playbook.  Molecule does not know about the
    Vagrant instances' configuration until the ``converge`` playbook is
    executed.

    Use the ``prepare`` playbook for any additional setup tasks you might require

    .. code-block:: yaml

        driver:
          name: custom_kubevirt
        platforms:
          - name: example-vm
            namespace: harvester-public
            rootFsName: root-fs
            rootFsSize: 10Gi
            rootFsAccessMode: "ReadWriteMany"
            rootFsVolumeMode: "Block"
            rootFsStorageClass: longhorn-image-pqsf2
            disks:
              - name: data
                accessMode: "ReadWriteMany"
                size: 15Gi
                #storageClass: omit
                volumeMode: "Block"
                fileSystem:
                  mount: true
                  type: xfs
                  path: /mnt/data

            arch: amd64
            cloudInit:
              type: cloudInitNoCloud
              userData:
              networkData:
            cores: 2
            cpuRatio: 0.5
            interfaceType: virtio
            interfaceMultus: hp-untagged #TODO Harvester specific
            interfaceName: enp1s0
            interfaces:
              - name: enp1s1
                type: virtio
                bridge: {}
            machineType: q35
            memory: 2Gi
            memoryRatio: 0.5
            secureBoot: false

    .. code-block:: bash

        $ python3 -m pip install molecule-plugins[kubevirt]

    When pulling from a private registry, it is the user's discretion to decide
    whether to use hard-code strings or environment variables for passing
    credentials to molecule.

    .. important::

        Hard-coded credentials in ``molecule.yml`` should be avoided, instead use
        `variable substitution`_.

    Provide a list of files Molecule will preserve, relative to the scenario
    ephemeral directory, after any ``destroy`` subcommand execution.

    .. code-block:: yaml

        driver:
          name: custom_kubevirt
          safe_files:
            - foo

    .. _`KubeVirt`: https://kubevirt.io/
    """

    def __init__(self, config=None) -> None:
        """Construct KubeVirt."""
        super().__init__(config)
        if config is not None:
            print(f"Run UUID: {config._run_uuid}")
            print(f"Scenarior: {config.scenario.name}")
            print(f"SDir: {config.scenario.directory}")
            print(f"EDir: {config.scenario.ephemeral_directory}")
            print(f"PDir: {config.project_directory}")
            print(f"PDirBN: {basename(config.project_directory)}")
        self._name = "custom-kubevirt"
        self._sanity_passed = False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def login_cmd_template(self):
        # TODO
        connection_options = " ".join(self.ssh_connection_options)

        return (
            "ssh {address} "
            "-l {user} "
            "-p {port} "
            "-i {identity_file} "
            f"{connection_options}"
        )

    @property
    def default_safe_files(self):
        # TODO
        return [
            self.instance_config,
            os.path.join(self._config.scenario.ephemeral_directory, ".vagrant")
        ]

    @property
    def default_ssh_connection_options(self):
        return self._get_ssh_connection_options()

    def login_options(self, instance_name):
        ic = self._get_instance_config(instance_name)
        log_opts = {
            "instance": instance_name,
            "address": ic["address"] if ic.get("address", "") else (
                self.get_instance_address(instance_name)),
            "user": ic.get("user"),
            "port": ic.get("port"),
            "identity_file": ic.get("identity_file"),
        }

        return log_opts

    def get_kubeconfig_file(self):
        driver = self._config.config.get("driver")
        if not driver:
            raise ValueError("Driver configuration is missing in Molecule configuration.")

        # Ensure `kubeconfig` is present and points to a valid file
        kubeconfig = driver.get("kubeconfig")
        if not kubeconfig:
            raise ValueError("Driver configuration is missing the 'kubeconfig' parameter.")

        # Resolve the path relative to the molecule.yml file
        kubeconfig_path = os.path.join(self._config.scenario.directory, kubeconfig)
        if not os.path.isfile(kubeconfig_path):
            raise FileNotFoundError(f"Kubeconfig file does not exist: {kubeconfig_path}")

        # Check if the file exists
        if not os.path.exists(kubeconfig_path):
            raise FileNotFoundError(f"Kubeconfig file not found at: {kubeconfig_path}")

        # Load kubeconfig using the constructed path
        return kubeconfig_path

    def get_instance_address(self, instance_name):
        ic = self._get_instance_config(instance_name)
        namespace = ic.get('namespace')
        pod_name = ic.get('pod_name')

        pod_ip_not_found = ValueError(f"Pod IP not found for pod {pod_name} in namespace {namespace}")

        try:
            vmi_ip = get_vmi_ip(pod_name,
                                namespace=namespace,
                                kubeconfig_path=self.get_kubeconfig_file(),
                                wait_for_lease=True,
                                )

            if not vmi_ip:
                raise pod_ip_not_found

        except TimeoutError as e:
            raise pod_ip_not_found

        return vmi_ip

    def ansible_connection_options(self, instance_name):
        try:
            ic = self._get_instance_config(instance_name)
            instance_address = ic["address"] if ic.get("address", "") else (
                self.get_instance_address(instance_name))

            options = {
                "ansible_user": "ubuntu", #d["user"],
                "ansible_password": "ubuntu",
                "ansible_host": instance_address,
                "ansible_port": ic["port"],
                "ansible_private_key_file": ic["identity_file"],
                "connection": "ssh",
                "ansible_ssh_common_args": " ".join(self.ssh_connection_options),
            }

            return options
        except StopIteration:
            return {}
        except OSError:
            # Instance has yet to be provisioned , therefore the
            # instance_config is not on disk.
            return {}

    def _get_instance_config(self, instance_name):
        instance_config_dict = util.safe_load_file(self._config.driver.instance_config)

        return next(
            item for item in instance_config_dict if item["instance"] == instance_name
        )

    def sanity_checks(self):
        print("Running sanity checks")
        """Implement Harvester driver sanity checks."""
        if self._sanity_passed:
            print("Sanity passed already")
            return

        log.info("Sanity checks: '%s'", self._name)
        # TODO(ssbarnea): reuse ansible runtime instance from molecule once it
        # fully adopts ansible-compat
        runtime = Runtime()
        if runtime.version < Version("2.10.0"):
            warnings.warn(
                f"Use of molecule-kubevirt with Ansible {runtime.version} is "
                "unsupported, upgrade to Ansible 2.11 or newer. "
                "Do not raise any bugs if your tests are failing with current configuration.",
                category=MoleculeRuntimeWarning,
            )

        driver = self._config.config.get("driver")
        if not driver:
            raise ValueError("Driver configuration is missing in Molecule configuration.")

        # Ensure `kubeconfig` is present and points to a valid file
        kc = self.get_kubeconfig_file()
        # make sure kubeconfig abs path was set

        self._sanity_passed = True

    @property
    def required_collections(self) -> dict[str, str]:
        """Return collections dict containing names and versions required."""
        return {
            "ansible.posix": "1.3.0",
            "kubernetes.core": "3",
        }

    def modules_dir(self):
        return os.path.join(os.path.dirname(__file__), "modules")


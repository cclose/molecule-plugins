import uuid

import yaml
import re
from dataclasses import dataclass, asdict
from typing import Optional

from molecule_plugins.kubevirt.modules.model.defaults import DefaultConfig


@dataclass
class InstanceConfig:
    """Represents a single instance configuration."""
    # SSH Properties
    instance: str
    run_id: str
    address: str = ""
    port: int = 22
    user: str = ""
    # K8S properties
    namespace: str = ""
    id: str = ""
    uid: str = ""
    # optional ssh props
    identity_file: Optional[str] = None
    password: Optional[str] = None

    # internal constants
    _POD_ID_LEN: int = 6
    _MAX_K8S_NAME_LEN: int = 63
    _MIN_DNS_NAME_LEN: int = 7 # 6 chars and hyphen

    def __post_init__(self):
        """
        Post Constructor that will make sure all generated fields are generated if they
        were not set in the constructor. This ensures require fields are set if called
        with incomplete data (missing instance_Config or from_name_and_run)
        """
        if not self.id:
            self.id = self.generate_instance_id()

    @staticmethod
    def generate_dns_name(name: str) -> str:
        # Ensure DNS-safe name: lowercase and replace invalid characters with '-'
        dns_safe_name = (re.sub(r'[^a-z0-9-]', '-', name.lower()))
        # remove leading or trailing '-'
        dns_safe_name = dns_safe_name.strip('-')

        return dns_safe_name

    @classmethod
    def generate_k8s_name(cls, dns_name: str, run_id: str, pod_id: str, run_name: str)\
            -> str:
        # Determine if truncation is needed for pod name
        if len(run_name) <= cls._MAX_K8S_NAME_LEN:
            k8s_name = run_name
            pod_suffix = f"-{run_id}" #TODO do we need this?

        else:
            # we'll append our run_id and pod_id to our pod so we can identify it
            pod_suffix = f"-{run_id}-{pod_id}"

            # Calculate max length for truncated DNS name
            # we subtract the length of our pod_suffix from the K8s Max to get how long
            # our "run name" can be
            max_len = cls._MAX_K8S_NAME_LEN - len(pod_suffix)
            truncated_dns_name = dns_name[:max_len]
            k8s_name = f"{truncated_dns_name}{pod_suffix}"

        return k8s_name

    @classmethod
    def generate_k8s_subresource_name(cls, sub_name: str, dns_name: str, run_id: str,
                                      pod_id: str) -> str:
        dns_sub_name = cls.generate_dns_name(sub_name)
        # Determine if truncation is needed for resource name
        item_name = f"{dns_name}-{dns_sub_name}-{run_id}"
        if len(item_name) > cls._MAX_K8S_NAME_LEN:
            # we'll append our run_id and pod_id to our pod so we can identify it
            pod_suffix = f"-{run_id}-{pod_id}"

            # Calculate max length for truncated name
            # we subtract the length of our pod_suffix from the K8s Max to get how long
            # our "run name" can be
            max_len = cls._MAX_K8S_NAME_LEN - len(pod_suffix)

            # we'll reserve space in the name for 6 characters and a - from the dns name
            # This might not actually truncate, the [:len] will return the original str
            # if it is shorter than len
            max_sub_name = max_len - cls._MIN_DNS_NAME_LEN
            truncated_sub_name = dns_sub_name[:max_sub_name]
            max_dns_name = max_len - (len(truncated_sub_name) + 1) # +1 for a hyphen!
            truncated_dns_name = dns_name[:max_dns_name]
            item_name = f"{truncated_dns_name}-{truncated_sub_name}{pod_suffix}"

        return item_name

    @classmethod
    def generate_instance_id(cls) -> str:
        return uuid.uuid4().hex

    @property
    def dns_name(self):
        return self.generate_dns_name(self.instance)

    @property
    def pod_id(self) -> str:
        return self.id[:self._POD_ID_LEN]

    @property
    def pod_name(self) -> str:
        return self.generate_k8s_name(self.dns_name, self.run_id, self.pod_id,
                                      self.run_name)

    @property
    def molecule_id(self) -> str:
        return f"{self.run_id}_{self.id}"

    def get_subresource_name(self, sub_name: str) -> str:
        return self.generate_k8s_subresource_name(sub_name, self.dns_name, self.run_id,
                                                  self.pod_id)

    @classmethod
    def from_dict(cls, data: dict):
        """ Convert a dictionary into an InstanceConfig object. """
        instance = cls(
            address=data['address'],
            instance=data['instance'],
            port=data['port'],
            user=data['user'],
            identity_file=data.get('identity_file'),
            password=data.get('password'),
            id=data['id'],
            namespace=data['namespace'],
            uid=data.get('uid'),
            run_id=data['run_id'],
        )

        # Sanity checks
        # Check if calculated fields match if they are in the data
        if data.get('dns_name'):
            if data['dns_name'] != instance.dns_name:
                raise ValueError(
                    f"Sanity check failed: provided 'dns_name' ({data['dns_name']}) does not match calculated "
                    f"'dns_name' ({instance.dns_name}).")

        if data.get('pod_name'):
            if data['pod_name'] != instance.pod_name:
                raise ValueError(
                    f"Sanity check failed: provided 'pod_name' ({data['pod_name']}) does not match calculated "
                    f"'pod_name' ({instance.pod_name}).")

        if data.get('pod_id'):
            if data['pod_id'] != instance.pod_id:
                raise ValueError(
                    f"Sanity check failed: provided 'pod_id' ({data['pod_id']}) does not match calculated 'pod_id' "
                    f"({instance.pod_id}).")

        if data.get('run_name'):
            if data['run_name'] != instance.run_name:
                raise ValueError(
                    f"Sanity check failed: provided 'run_name' ({data['run_name']}) does not match calculated "
                    f"'run_name' ({instance.run_name}).")

        return instance

    @classmethod
    def from_name_and_run(cls, name: str, run_id: str, namespace: str=None,
                          defaults: DefaultConfig=None):
        return cls(
            instance=name,
            run_id=run_id,
            namespace=namespace if namespace is not None else None,
            port=int(defaults.ssh_port) if defaults is not None else None,
            user=defaults.ssh_user if defaults is not None else None,
        )

    @property
    def run_name(self):
        return f"{self.dns_name}-{self.run_id}"

    @property
    def pod_suffix(self):
        return f"-{self.run_id}-{self.pod_id}"

    def to_dict(self) -> dict:
        """ Convert the InstanceConfig to a dictionary. """
        return {
            'instance': self.instance,
            'address': self.address,
            'user': self.user,
            'port': self.port,
            'identity_file': self.identity_file,
            'password': self.password,
            'dns_name': self.dns_name,
            'namespace': self.namespace,
            'id': self.id,
            'uid': self.uid,
            'pod_id': self.pod_id,
            'pod_name': self.pod_name,
            'run_id': self.run_id
        }


@dataclass
class InstanceConfigList:
    """
    Represents a list of InstanceConfig objects.
    """
    instance_configs: list[InstanceConfig]

    def get_instance(self, instance_name: str) -> Optional[InstanceConfig]:
        # Loops instances and returns the first one that has a matching name
        return next((instance for instance in self.instance_configs
                     if instance.instance == instance_name), None)

    def get_instance_by_molecule_id(self, molecule_id: str) -> Optional[InstanceConfig]:
        # Loops instances and returns the first one that has a matching molecule_id
        return next((instance for instance in self.instance_configs
                     if instance.molecule_id == molecule_id), None)

    @classmethod
    def from_yaml(cls, yaml_content: str):
        """Load a list of InstanceConfig objects from a YAML string."""
        data = yaml.safe_load(yaml_content)
        instance_configs = [InstanceConfig.from_dict(item) for item in data]
        return cls(instance_configs)

    def to_yaml(self) -> str:
        """Convert the list of InstanceConfig objects to a YAML string."""
        return yaml.dump([config.to_dict() for config in self.instance_configs], default_flow_style=False)

    @classmethod
    def from_dict(cls, data: list):
        """
        The method is called "from dict" but it's actually "from list". We just call it
        dict because it's a list of dicts and it's simpler to think that way
        """
        ic_list = []
        for item in data:
            ic_list.append(InstanceConfig.from_dict(item))

        return cls(ic_list)

    def to_dict(self) -> dict:
        return {
            'instance_configs': self.to_list()
        }

    def to_list(self) -> list:
        return [item.to_dict() for item in self.instance_configs]

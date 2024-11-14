from dataclasses import dataclass, field
from typing import List, Optional, Dict

from molecule_plugins.kubevirt.modules.model.common import DataClassDictValidatorMixin
from molecule_plugins.kubevirt.modules.model.defaults import DefaultConfig
from abc import ABC, abstractmethod


@dataclass
class FileSystemConfig(DataClassDictValidatorMixin):
    mount: bool = False
    type: str = "ext4"
    path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict, defaults: DefaultConfig) -> "FileSystemConfig":
        cls.validate_dict_keys(data)
        return cls(
            mount=data.get("mount"),
            type=data.get("type"),
            path=data.get("path", None),
        )

@dataclass
class DiskConfig(DataClassDictValidatorMixin):
    name: str
    accessMode: str
    size: str
    type: str
    volumeMode: str
    storageClass: Optional[str] = None
    fileSystem: Optional[FileSystemConfig] = None

    REQUIRED_KEYS = {"name"}

    @classmethod
    def from_dict(cls, data: dict, defaults: DefaultConfig) -> "DiskConfig":
        cls.validate_dict_keys(data, cls.REQUIRED_KEYS)

        # Use FileSystemConfig.from_dict if "fileSystem" key is present
        file_system = FileSystemConfig.from_dict(data["fileSystem"], defaults) \
            if "fileSystem" in data else None

        return cls(
            name=data["name"],
            accessMode=data.get("accessMode", defaults.disk_access_mode),
            size=data.get("size", defaults.disk_size),
            type=data.get("type", defaults.disk_type),
            volumeMode=data.get("volumeMode", defaults.disk_volume_mode),
            storageClass=data.get("storageClass", None),
            fileSystem=file_system,
        )

@dataclass
class CloudInitConfig:
    type: str
    userData: Optional[str] = None
    networkData: Optional[str] = None

@dataclass
class InterfaceConfig(DataClassDictValidatorMixin):
    name: str
    type: str
    bridge: Optional[Dict] = field(default_factory=dict)
    multus: Optional[str] = None

    REQUIRED_KEYS = {"name"}

    @classmethod
    def from_dict(cls, data: dict, defaults: DefaultConfig) -> "InterfaceConfig":
        cls.validate_dict_keys(data, cls.REQUIRED_KEYS)

        return cls(
            name=data['name'],
            type=data.get('type', defaults.interface_type),
            bridge=data.get('bridge', {}) if 'bridge' in data else None,
            multus=data.get('multus', None) if 'multus' in data else None,
        )


@dataclass
class PlatformConfig(DataClassDictValidatorMixin):
    """ """
    # Properties aren't proper python snake_case so that they match the YAML keys
    # which are meant to reflect the Kubernetes Yaml style
    name: str
    namespace: str
    rootFsName: str
    rootFsSize: str
    rootFsAccessMode: str
    rootFsType: str
    rootFsVolumeMode: str
    rootFsStorageClass: Optional[str]
    disks: List[DiskConfig]
    arch: str
    cloudInit: Optional[CloudInitConfig]
    cores: int
    cpuRatio: float
    interfaceType: str
    interfaceMultus: Optional[str]
    interfaceName: str
    interfaces: List[InterfaceConfig]
    machineType: str
    memory: str
    memoryRatio: float
    secureBoot: bool

    REQUIRED_KEYS = { "name", "rootFsStorageClass" }

    @classmethod
    def from_dict(cls, data: dict, defaults: DefaultConfig) -> "PlatformConfig":
        cls.validate_dict_keys(data, cls.REQUIRED_KEYS)
        # Verify uniqueness of name
        if "rootFsStorageClass" not in data:
            # TODO in the future we can be more flexible about how root-fs sources it's
            # image data, but right now we only support storageClasses
            raise ValueError('platform item is missing required "rootFsStorageClass" '
                             'field. Will be unable to set Operating System without')
        return cls(
            # Required
            name=data["name"],
            rootFsStorageClass=data.get("rootFsStorageClass"),
            # Optional
            namespace=data.get("namespace", defaults.namespace),
            rootFsName=data.get("rootFsName", defaults.root_fs_name),
            rootFsSize=data.get("rootFsSize", defaults.disk_size),
            rootFsAccessMode=data.get("rootFsAccessMode",
                                         defaults.disk_access_mode),
            rootFsType=data.get("rootFsType", defaults.disk_type),
            rootFsVolumeMode=data.get("rootFsVolumeMode",
                                         defaults.disk_volume_mode),
            #disks=[DiskConfig(**disk) for disk in platform_data.get("disks", [])],
            disks=[DiskConfig.from_dict(disk, defaults) for disk in
                   data.get("disks", [])],
            arch=data.get("arch", defaults.arch),
            cloudInit=CloudInitConfig(
                type=data.get("cloudInit",
                              {}).get("type", defaults.cloud_init_type),
                userData=data.get("cloudInit", {}).get("userData"),
                networkData=data.get("cloudInit", {}).get("networkData")
            ) if "cloudInit" in data else None,
            cores=data.get("cores", defaults.cores),
            cpuRatio=data.get("cpuRatio", defaults.cpu_ratio),
            interfaceType=data.get("interfaceType",
                                    defaults.interface_type),
            interfaceMultus=data.get("interfaceMultus"),
            interfaceName=data.get("interfaceName",
                                    defaults.interface_name),
            interfaces=[InterfaceConfig.from_dict(iface, defaults) for iface in
                        data.get("interfaces", [])],
            machineType=data.get("machineType", defaults.machine_type),
            memory=data.get("memory", defaults.memory),
            memoryRatio=data.get("memoryRatio", defaults.memory_ratio),
            secureBoot=data.get("secureBoot", defaults.secure_boot),
        )


@dataclass
class PlatformConfigList:
    platform_configs: list[PlatformConfig]

    @classmethod
    def from_dict(cls, data: list[dict], defaults: DefaultConfig) -> "PlatformConfigList": # noqa: ES501
        instance_names = dict()
        platform_configs = []
        for platform_data in data:
            pc = PlatformConfig.from_dict(platform_data, defaults)
            # Verify uniqueness of name
            if pc.name in instance_names:
                raise ValueError(f'duplicate name: {platform_data["name"]}')
            instance_names[pc.name] = None

            platform_configs.append(pc)

        return cls(platform_configs=platform_configs)

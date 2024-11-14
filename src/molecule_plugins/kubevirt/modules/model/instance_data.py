from typing import Optional
from dataclasses import dataclass
from molecule_plugins.kubevirt.modules.model.common import DictParserMixin
from molecule_plugins.kubevirt.modules.model.instance_config import InstanceConfig
from molecule_plugins.kubevirt.modules.model.platform_config import PlatformConfig
from base64 import b64encode

from poetry.console.commands import self


@dataclass
class InstanceDiskBus(DictParserMixin):
    bus: str

@dataclass
class InstanceDisk(DictParserMixin):
    name: str
    disk: InstanceDiskBus

@dataclass
class InstanceInterface(DictParserMixin):
    name: str
    model: str
    bridge: dict

@dataclass
class InstanceMultus(DictParserMixin):
    networkName: str

@dataclass
class InstanceNetwork(DictParserMixin):
    name: str
    multus: Optional[InstanceMultus]

@dataclass
class InstancePVC(DictParserMixin):
    name: str
    accessMode: str
    size: str
    storageClass: str
    volumeMode: str

@dataclass
class InstanceVolumePVC(DictParserMixin):
    claimName: str

@dataclass
class InstanceCloudInit():
    userData: Optional[str] = None
    networkData: Optional[str] = None
    userDataBase64: Optional[str] = None
    networkDataBase64: Optional[str] = None

    def to_dict(self):
        data = {}
        if self.userData is not None:
            data['userData'] = self.userData
        if self.networkData is not None:
            data['networkData'] = self.networkData
        if self.userDataBase64 is not None:
            data['userDataBase64'] = self.userDataBase64
        if self.networkDataBase64 is not None:
            data['networkDataBase64'] = self.networkDataBase64

        return data

    @classmethod
    def from_dict(cls, data: dict):
        # Create an instance of InstanceCloudInit from a dictionary
        return cls(
            userData=data.get("userData"),
            networkData=data.get("networkData"),
            userDataBase64=data.get("userDataBase64"),
            networkDataBase64=data.get("networkDataBase64")
        )


@dataclass
class InstanceVolume:
    name: str
    persistentVolumeClaim: Optional[InstanceVolumePVC] = None
    cloudInitNoCloud: Optional[InstanceCloudInit] = None

    def to_dict(self):
        data = {
            "name": self.name,
        }

        if self.persistentVolumeClaim is not None:
            data["persistentVolumeClaim"] = self.persistentVolumeClaim.to_dict()
        if self.cloudInitNoCloud is not None:
            data["cloudInitNoCloud"] = self.cloudInitNoCloud.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: dict):
        # Special handling for nested classes
        pvc_data = data.get("persistentVolumeClaim")
        cloud_init_data = data.get("cloudInitNoCloud")
        return cls(
            name=data["name"],
            persistentVolumeClaim=InstanceVolumePVC.from_dict(pvc_data) if pvc_data else None,
            cloudInitNoCloud=InstanceCloudInit.from_dict(cloud_init_data) if cloud_init_data else None
        )

@dataclass
class InstanceData(DictParserMixin):
    """
    Represents the Data for an instance need to deploy K8S resources
    """
    name: str
    dns_safe_name: str
    run_name: str
    pod_name: str
    molecule_id: str
    disks: list[InstanceDisk]
    interfaces: list[InstanceInterface]
    networks: list[InstanceNetwork]
    pvcs: list[InstancePVC]
    volumes: list[InstanceVolume]

    def to_dict(self):
        return {
            "name": self.name,
            "dns_safe_name": self.dns_safe_name,
            "run_name": self.run_name,
            "pod_name": self.pod_name,
            "molecule_id": self.molecule_id,
            "disks": [disk.to_dict() for disk in self.disks if disk is not None],
            "interfaces": [iface.to_dict() for iface in self.interfaces if iface is not None],
            "networks": [network.to_dict() for network in self.networks if network is not None],
            "pvcs": [pvc.to_dict() for pvc in self.pvcs if pvc is not None],
            "volumes": [volume.to_dict() for volume in self.volumes if volume is not None],
        }

    @classmethod
    def from_config(cls, ic: InstanceConfig, pc: PlatformConfig):
        disks = [
            InstanceDisk(
                name=pc.rootFsName,
                disk=InstanceDiskBus(
                    bus=pc.rootFsType,
                )
            )
        ]
        interfaces = [
            InstanceInterface(
                name=pc.interfaceName,
                model=pc.interfaceType,
                bridge={},
            )
        ]
        networks = [
            InstanceNetwork(
                name=pc.interfaceName,
                multus=InstanceMultus(networkName=pc.interfaceMultus) if pc.interfaceMultus is not None else None,
            )
        ]
        pvcs = [
            InstancePVC(
                name=ic.get_subresource_name(pc.rootFsName),
                accessMode=pc.rootFsAccessMode,
                size=pc.rootFsSize,
                storageClass=pc.rootFsStorageClass,
                volumeMode=pc.rootFsVolumeMode,
            )
        ]
        volumes = [
            InstanceVolume(
                name=pc.rootFsName,
                persistentVolumeClaim=InstanceVolumePVC(
                    claimName=ic.get_subresource_name(pc.rootFsName),
                )
            )
        ]

        for disk in pc.disks:
            disks.append(InstanceDisk(
                name=disk.name,
                disk=InstanceDiskBus(
                    bus=disk.type
                )
            ))
            pvcs.append(InstancePVC(
                name=ic.get_subresource_name(disk.name),
                accessMode=disk.accessMode,
                size=disk.size,
                storageClass=disk.storageClass,
                volumeMode=disk.volumeMode,
            ))
            volumes.append(InstanceVolume(
                name=disk.name,
                persistentVolumeClaim=InstanceVolumePVC(
                    claimName=ic.get_subresource_name(disk.name),
                )
            ))

        if pc.cloudInit is not None:
            volumes.append(InstanceVolume(
                name="cloudinitdisk",
                cloudInitNoCloud=InstanceCloudInit(
                    userDataBase64=b64encode(pc.cloudInit.userData.encode("utf-8"))
                    if pc.cloudInit.userData else None,
                    networkDataBase64=b64encode(pc.cloudInit.networkData.encode("utf-8"))
                    if pc.cloudInit.networkData else None,
                ) if pc.cloudInit.type == "cloudInitNoCloud" else None,
            ))

        for iface in pc.interfaces:
            interfaces.append(InstanceInterface(
                name=iface.name,
                model=iface.type,
                bridge=iface.bridge if iface.bridge is not None else None,
            ))
            networks.append(InstanceNetwork(
                name=iface.name,
                multus=InstanceMultus(networkName=iface.multus) if iface.multus is not None else None,
            ))

        return cls(
            name=ic.instance,
            dns_safe_name=ic.dns_name,
            run_name=ic.run_name,
            pod_name=ic.pod_name,
            molecule_id=ic.molecule_id,
            disks=disks,
            interfaces=interfaces,
            networks=networks,
            pvcs=pvcs,
            volumes=volumes
        )



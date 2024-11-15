from dataclasses import dataclass, asdict

@dataclass
class DefaultConfig:
    arch: str = "amd64"
    cloud_init_type: str = "cloudInitNoCloud"
    cores: int = 2
    disk_access_mode: str = "ReadWriteMany"
    disk_size: str = "10Gi"
    disk_type: str = "virtio"
    disk_volume_mode: str = "Block"
    interface_name: str = "enp1s0"
    interface_type: str = "virtio"
    machine_type: str = "q35"
    memory: str = "2Gi"
    namespace: str = "default"
    root_fs_name: str = "rootfs"
    secure_boot: bool = False
    ssh_port: str = "22"
    ssh_user: str = "ubuntu"
    memory_ratio: float = 0.5
    cpu_ratio: float = 0.5


    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)
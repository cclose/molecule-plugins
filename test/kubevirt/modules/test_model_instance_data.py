import pytest
from molecule_plugins.kubevirt.modules.model.defaults import DefaultConfig
from molecule_plugins.kubevirt.modules.model.instance_config import InstanceConfig
from molecule_plugins.kubevirt.modules.model.instance_data import InstanceData, InstanceDisk, InstanceDiskBus, \
    InstanceInterface, InstanceNetwork, InstancePVC, InstanceVolume, InstanceVolumePVC, InstanceCloudInit


def test_instance_data_to_dict():
    defaults = DefaultConfig.from_dict({})
    ic = InstanceConfig.from_name_and_run("test", "trun01")
    id = InstanceData(
        name=ic.instance,
        dns_safe_name=ic.dns_name,
        run_name=ic.run_name,
        pod_name=ic.pod_name,
        disks=[
            InstanceDisk(
                name="root-fs",
                disk=InstanceDiskBus(bus="virtio"),
            ),
            InstanceDisk(
                name="data",
                disk=InstanceDiskBus(bus="virtio"),
            ),
        ],
        interfaces=[
            InstanceInterface(
                name=defaults.interface_name,
                bridge={},
                model=defaults.interface_type,
            )
        ],
        networks=[
            InstanceNetwork(
                name=defaults.interface_name,
            ),
        ],
        pvcs=[
            InstancePVC(
                name=ic.get_subresource_name("root-fs-pvc"),
                accessMode=defaults.disk_access_mode,
                size=defaults.disk_size,
                storageClass="harvester-dv-ubuntu22",
                volumeMode=defaults.disk_volume_mode,
            ),
            InstancePVC(
                name=ic.get_subresource_name("data-pvc"),
                accessMode=defaults.disk_access_mode,
                size=defaults.disk_size,
                storageClass="harvester",
                volumeMode=defaults.disk_volume_mode,
            ),
        ],
        volumes=[
            InstanceVolume(
                name="root-fs",
                persistentVolumeClaim=InstanceVolumePVC(
                    claimName=ic.get_subresource_name("root-fs-pvc"),
                ),
            ),
            InstanceVolume(
                name="data",
                persistentVolumeClaim=InstanceVolumePVC(
                    claimName=ic.get_subresource_name("data-pvc"),
                ),
            ),
            InstanceVolume(
                name="cloudinitdisk",
                cloudInitNoCloud=InstanceCloudInit(
                    userDataBase64=b"I2Nsb3VkLWNvbmZpZwpwYXNzd29yZDogbW9sZWN1bGUKY2hwYXNzd2Q6IHsgZXhwaXJlOiBGYWxzZSB9CnNzaF9wd2F1dGg6IFRydWUKcGFja2FnZV91cGRhdGU6IHRydWUKcGFja2FnZV91cGdyYWRlOiB0cnVlCgpjaHBhc3N3ZDoKICBsaXN0OiB8CiAgICB1YnVudHU6dWJ1bnR1CiAgZXhwaXJlOiBmYWxzZQoKcGFja2FnZXM6CiAgLSBjdXJsCiAgLSBnaXQKICAtIG9wZW5zc2wKICAtIHB5dGhvbjMKICAtIHB5dGhvbjMtYXB0CiAgLSBxZW11LWd1ZXN0LWFnZW50CiAgLSB3Z2V0Cg" # noqa: ES501
                )
            )
        ]
    )

    id_dict = id.to_dict()
    print(id_dict)
    assert isinstance(id_dict, dict)

def test_instance_data_from_dict():
    id_dict = {
        'name': 'test',
         'dns_safe_name': 'test',
         'run_name': 'test-trun01',
         'pod_name': 'test-trun01',
         'disks': [
             {
                 'name': 'root-fs',
                 'disk': {'bus': 'virtio'}
              },
             {
                'name': 'data',
                'disk': {'bus': 'virtio'}
             }
         ],
         'interfaces': [
             {
                 'name': 'enp1s0',
                 'model': 'virtio',
                 'bridge': {}
             }
         ],
         'networks': [
             {
                 'name': 'enp1s0'
             }
         ],
         'pvcs': [
             {
                 'name': 'test-root-fs-pvc-trun01',
                 'accessMode': 'ReadWriteMany',
                 'size': '10Gi',
                 'storageClass': 'harvester-dv-ubuntu22',
                 'volumeMode': 'Block'
             },
             {
                 'name': 'test-data-pvc-trun01',
                 'accessMode': 'ReadWriteMany',
                 'size': '10Gi',
                 'storageClass': 'harvester',
                 'volumeMode': 'Block'
             }
         ],
         'volumes': [
             {
                 'name': 'root-fs',
                 'persistentVolumeClaim': {
                     'claimName': 'test-root-fs-pvc-trun01'
                 }
             },
             {
                 'name': 'data',
                 'persistentVolumeClaim': {
                     'claimName': 'test-data-pvc-trun01'
                 }
             }
         ]
    }

    id = InstanceData.from_dict(id_dict)
    assert isinstance(id, InstanceData)

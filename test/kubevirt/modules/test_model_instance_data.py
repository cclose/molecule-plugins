import pytest
from humanfriendly import InvalidSize

from molecule_plugins.kubevirt.modules.model.defaults import DefaultConfig
from molecule_plugins.kubevirt.modules.model.instance_config import InstanceConfig
from molecule_plugins.kubevirt.modules.model.instance_data import InstanceData, InstanceDisk, InstanceDiskBus, \
    InstanceInterface, InstanceNetwork, InstancePVC, InstanceVolume, InstanceVolumePVC, InstanceCloudInit
from molecule_plugins.kubevirt.modules.model.platform_config import PlatformConfig
from molecule_plugins.kubevirt.modules.model.run_config import RunConfig


def test_instance_data_to_dict():
    defaults = DefaultConfig.from_dict({})
    ic = InstanceConfig.from_name_and_run("test", "trun01")
    id = InstanceData(
        name=ic.instance,
        dns_safe_name=ic.dns_name,
        run_name=ic.run_name,
        pod_name=ic.pod_name,
        molecule_id=ic.molecule_id,
        arch=defaults.arch,
        cores=defaults.cores,
        cpuRatio=defaults.cpu_ratio,
        machineType=defaults.machine_type,
        memory=defaults.memory,
        memoryRatio=defaults.memory_ratio,
        namespace=defaults.namespace,
        secureBoot=defaults.secure_boot,
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
                diskName="root-fs",
                accessMode=defaults.disk_access_mode,
                size=defaults.disk_size,
                storageClass="harvester-dv-ubuntu22",
                volumeMode=defaults.disk_volume_mode,
            ),
            InstancePVC(
                name=ic.get_subresource_name("data-pvc"),
                diskName="root-fs",
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
        'molecule_id': 'run123_3409sdf093290as2',
        'arch': 'amd64',
        'cores': 4,
        'cpuRatio': 0.5,
        'machineType': 'q35',
        'memory': '3Gi',
        'memoryRatio': 0.5,
        'namespace': 'molecule',
        'secureBoot': False,
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


@pytest.mark.parametrize(
    ("input", "output", "ratio", "fail"),
    [
        ( "1Mi", "512Ki", 0.5, False),
        ( "100M", "47.68Mi", 0.5, False),
        ( "100Mi", "75Mi", 0.75, False),
        ( "100MB", "95.37Mi", 1, False),
        ( "100MiB", "100Mi", 1, False),
        ( "10", None, 1, True),
    ]
)
def test_instance_data_memory_requests(input, output, ratio, fail):
    pcd = {
        "name": "test",
        "rootFsStorageClass": "test",
        "memoryRatio": ratio,
        "memory": input,
    }
    defaults = DefaultConfig.from_dict({})
    ic = InstanceConfig.from_name_and_run("test", "trun01")
    pc = PlatformConfig.from_dict(pcd, defaults)
    rc = RunConfig.new("unittest", "utest", "test_instancedata")
    id = InstanceData.from_config(ic, pc, rc)
    assert isinstance(id, InstanceData)

    try:
        mReq = id.memory_requests
        assert mReq == output
        assert not fail
    except InvalidSize as ise:
        assert fail



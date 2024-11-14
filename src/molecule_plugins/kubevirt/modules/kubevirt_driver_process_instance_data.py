from ansible.module_utils.basic import AnsibleModule
from uuid import uuid4
import re
import base64

import molecule_plugins.kubevirt.modules.model.instance_data
from molecule_plugins.kubevirt.modules.model.instance_config import InstanceConfig
from molecule_plugins.kubevirt.modules.model.instance_data import InstancePVC, InstanceData
from molecule_plugins.kubevirt.modules.model.platform_config \
    import PlatformConfig, PlatformConfigList
from molecule_plugins.kubevirt.modules.model.defaults import DefaultConfig

DOCUMENTATION = """
---
module: kubevirt_driver_process_instance_data
short_description: Merge instance_config, platform_config, and run_config data.
description:
    -
author:
    - Cory Close (@cclose)
version_added: "2.10"
requirements:
    - python >= 3.6
    - PyYAML
options:
    action:
        description:
            - The action to perform
            - - prepare: merges instance_config, run_config, and platform_config and 
                         sets up necessary data structures for deployment.
            - - parse_drive: parses deployment details from a deployed instance volume
            - - parse_instance: parses deployment details from a deployed instance
        type: str
        choices: ["prepare", "parse_drive", "parse_instance"]
        required: true
    instance_config:
        description:
            - parsed instance_config data from prior runs
        type: list
        required: false
        default: list()
    instance_data:
        description:
            - instance deployment data that has already been prepared by "prepare"
            - - used when updating / parsing
        type: list
        required: false
        default: list()
    run_config:
        description:
            - configuration and identifier info for the current molecule run
        type: dict
        required: false
        default: dict()
    platform_config:
        description:
            - passed desired configuration for molecule infrastructure from the
              molecule.yml file, platform section.
        type: list
        required: false
        default: list()
supports_check_mode: true
notes:
    - In check mode, no files are modified, but it will simulate the changes and set the "changed" status accordingly.
"""

EXAMPLES = """
- name: Prepare instance configuration
  kubevirt_driver_process_instance_data:
    action: prepare
    instance_config: "{{ instance_config.instance_config }}"
    platform_config: "{{ instances }}"
    run_config: "{{ run_config }}"
  register: instance_data

- name: Parse deployment details from a deployed instance volume
  kubevirt_driver_process_instance_data:
    action: parse_drive
    instance_config: "{{ instance_config.instance_config }}"
    platform_config: "{{ instances }}"
    run_config: "{{ run_config }}"
"""

RETURN = """
instance_data:
    description: The parsed and loaded instance deployment data
    type: dict
    returned: when action is "load"
changed:
    description: Indicates whether the configuration file was modified.
    type: bool
    returned: always
msg:
    description: A message indicating the result of the action (e.g., success, failure, check mode).
    type: str
    returned: always
"""

MAX_K8S_NAME_LEN = 63

def prepare_instance_data(instance_config, platform_config, run_config, default_config={}):

    defaults = DefaultConfig.from_dict(default_config)
    run_id = run_config.get("run_id", None)
    instance_data_list = []
    platform_data = PlatformConfigList.from_dict(platform_config, defaults)

    for instance in platform_data.platform_configs:
        name = instance.name
        # look for a matching instance_config
        plat_ic = next((ic for ic in instance_config if ic.get("name") == name), None)
        # TODO fail parsing
        if plat_ic is not None:
            p_ic = InstanceConfig.from_dict(plat_ic)
        else:
            p_ic = InstanceConfig.from_name_and_run(name, run_id)

        instance_data = InstanceData.from_config(p_ic, instance)

        #root_fs_name = instance.rootFsName
        #root_pvc_name = p_ic.get_subresource_name(root_fs_name)
        #instance_data = InstanceData(
        #    name=name,
        #    dns_safe_name=p_ic.dns_name,
        #    run_name=p_ic.run_name,

        #)
        #instance_data = {
        #    "name": name,
        #    "dns_safe_name": p_ic.dns_name,
        #    "run_name": p_ic.run_name,
        #    "pod_name": p_ic.pod_name,
        #    # TODO? "_pod_suffix": pod_suffix
        #    "disks": [
        #        {
        #            "disk": {
        #                "bus": instance.rootFsType,
        #            },
        #            "name": root_fs_name,
        #        },
        #    ],
        #    "pvcs": [
        #        {
        #            "name": root_pvc_name,
        #            "molecule_id": p_ic.molecule_id,
        #            "accessMode": instance.rootFsAccessMode,
        #            "size": instance.rootFsSize,
        #            "storageClass": instance.rootFsStorageClass,
        #            "volumeMode": instance.rootFsVolumeMode,
        #        }
        #    ],
        #    "volumes": [
        #        {
        #            "name": root_fs_name,
        #            "persistentVolumeClaim": {
        #                "claimName": root_pvc_name,
        #            },
        #        }
        #    ],
        #    "interfaces": [
        #        {
        #            "bridge": {},
        #            "model": instance.interfaceType,
        #            "name": instance.interfaceName,
        #        },
        #    ],
        #    "networks": [
        #        {
        #            "name": instance.interfaceName,
        #        },
        #    ]
        #}

        #if instance.interfaceMultus:
        #    instance_data["networks"][0]["multus"] = {
        #        "networkName": instance.interfaceMultus,
        #    }

        #for disk in instance.disks:
        #    disk_pvc_name = p_ic.get_subresource_name(disk.name)
        #    disk_dict = {
        #        "disk": {
        #            "bus": disk.type,
        #        },
        #        "name": disk.name,
        #    }
        #    instance_data["disks"].append(disk_dict)
        #    pvc_dict = {
        #        "namespace": instance.namespace,
        #        "name": disk_pvc_name,
        #        "molecule_id": p_ic.get_molecule_id(),
        #        "accessMode": disk.accessMode,
        #        "size": disk.size,
        #        "storageClass": disk.storageClass, #TODO else omit?? else default??
        #        "volumeMode": disk.volumeMode,
        #    }
        #    instance_data["pvcs"].append(pvc_dict)
        #    vol_dict = {
        #        "persistentVolumeClaim": {
        #            "name": disk_pvc_name,
        #        },
        #        "name": disk.name,
        #    }
        #    instance_data["volumes"].append(vol_dict)

        #for iface in instance.interfaces:
        #    iface_dict = {
        #        "model": iface.type,
        #        "name": iface.name,
        #    }
        #    if iface.bridge:
        #        iface_dict["bridge"] = iface.bridge,
        #    instance_data["interfaces"].append(iface_dict)

        #    net_dict = {
        #        "name": iface.name,
        #    }
        #    if iface.multus:
        #        net_dict["multus"] = {
        #            "networkName": iface.multus,
        #        }
        #    instance_data["networks"].append(net_dict)

        #if instance.cloudInit:
        #    cloud_init = instance.cloudInit
        #    cloud_init_data = {}
        #    if cloud_init.userData:
        #        user_data = cloud_init.userData.encode("utf-8")
        #        cloud_init_data["userDataBase64"] = base64.b64encode(user_data)
        #    if cloud_init.networkData:
        #        net_data = cloud_init.networkData.encode("utf-8")
        #        cloud_init_data["networkDataBase64"] = base64.b64encode(net_data)
        #    cloud_init_vol = {
        #        "name": "cloudinitdisk",
        #        cloud_init.type: cloud_init_data
        #    }

        #    instance_data["volumes"].append(cloud_init_vol)

        instance_data_list.append(instance_data.to_dict())

    return instance_data_list


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type="str", choices=["prepare", "parse_drive", "parse_instance"], required=True),
            default_config=dict(type="dict", required=False),
            instance_config=dict(type="list", required=False),
            instance_data=dict(type="list", required=False),
            run_config=dict(type="dict", required=False),
            platform_config=dict(type="list", required=False),
        ),
        supports_check_mode=True
    )

    result = dict(
        changed=False,
    )

    # Extract global parameters
    action = module.params["action"]
    check_mode = module.check_mode

    instance_yml = ""

    try:
        if action == "prepare":
            # TODO instance_config, run_config, platform_config
            if 'instance_config' not in module.params:
                module.fail_json(msg="'instance_config' is required when 'action' is"
                                     " 'prepare'")
            if 'platform_config' not in module.params:
                module.fail_json(msg="'platform_config' is required when 'action' is"
                                     " 'prepare'")
            if 'run_config' not in module.params:
                module.fail_json(msg="'run_config' is required when 'action' is "
                                     "'prepare'")

            defaults = {}
            if 'default_config' in module.params:
                defaults = module.params['default_config']
            instance_config = module.params["instance_config"]
            platform_config = module.params["platform_config"]
            run_config = module.params["run_config"]

            data = prepare_instance_data(instance_config, platform_config, run_config,
                                         defaults)
            module.exit_json(changed=True, instance_data=data,
                             msg="Instance Data Prepared")

            pass

        elif action == "parse_drive":
            pass

        elif action == "parse_instance":
            pass

        else:
            raise ValueError(f"Invalid `action` parameter: {action}")

    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}")

    module.exit_json(**result)


if __name__ == "__main__":
    main()

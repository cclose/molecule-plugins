from ansible.module_utils.basic import AnsibleModule
from uuid import uuid4
import re
import base64

import molecule_plugins.kubevirt.modules.model.instance_data
from molecule_plugins.kubevirt.modules.model.instance_config \
    import InstanceConfig, InstanceConfigList
from molecule_plugins.kubevirt.modules.model.instance_data \
    import InstancePVC, InstanceData
from molecule_plugins.kubevirt.modules.model.platform_config \
    import PlatformConfig, PlatformConfigList
from molecule_plugins.kubevirt.modules.model.defaults import DefaultConfig
from molecule_plugins.kubevirt.modules.model.run_config import RunConfig

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
            - - parse_instance: parses deployment details from a deployed instance
        type: str
        choices: ["prepare", "parse_instance"]
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

- name: Parse deployment details from a deployed instance
  kubevirt_driver_process_instance_data:
    action: parse_instance
    instance_config: "{{ instance_config.instance_config }}"
    instance_data: "{{ instances }}"
    drive_data: "{{ drives }}"
"""

RETURN = """
instance_config:
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

def prepare_instance_data(instance_config, platform_config, run_config, default_config=None):

    if default_config is None:
        default_config = {}

    defaults = DefaultConfig.from_dict(default_config)
    rc = RunConfig.from_dict(run_config)
    run_id = run_config.get("run_id", None)
    # Todo deal with None Run_Id
    platform_data = PlatformConfigList.from_dict(platform_config, defaults)
    ic_list = InstanceConfigList.from_dict(instance_config)
    instance_data_list = []

    for instance in platform_data.platform_configs:
        name = instance.name
        # look for a matching instance_config
        ic = ic_list.get_instance(name)
        if ic is None:
            ic = InstanceConfig.from_name_and_run(name, rc.run_id,
                                                  namespace=instance.namespace,
                                                  defaults=defaults)
            ic_list.instance_configs.append(ic)

        instance_data = InstanceData.from_config(ic, instance, rc=rc)

        instance_data_list.append(instance_data.to_dict())
        # If we have an identity file set, add it to the instance config
        if rc.ssh_key_path:
            ic.identity_file = rc.ssh_key_path

    return instance_data_list, ic_list.to_list()

def parse_instance_results(instance_config, instance_data):
    icl = InstanceConfigList.from_dict(instance_config)

    for item in instance_data:
        result = item.get('result')
        if not result:
            continue  # Skip items without a 'result'

        metadata = result.get('metadata')
        if not metadata:
            continue  # Skip items without 'metadata'

        molecule_id = _extract_molecule_id(metadata)
        ic = icl.get_instance_by_molecule_id(molecule_id)
        if not ic:
            raise ValueError(f"InstanceConfig for Molecule ID not found: {molecule_id}")

        uid = metadata.get('uid')
        if not uid:
            raise ValueError(f"UID not found in return data for Molecule ID: {molecule_id}")

        ic.uid = uid

        #TODO find and parse address
    return icl


def _extract_molecule_id(metadata):
    """Helper to extract molecule_id from metadata labels."""
    labels = metadata.get('labels')
    if not labels or 'molecule_id' not in labels:
        raise ValueError(f"molecule_id not found in return metadata")
    return labels['molecule_id']




def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type="str", choices=["prepare", "parse_instance"], required=True),
            default_config=dict(type="dict", required=False),
            instance_config=dict(type="list", required=False),
            instance_data=dict(type="list", required=False),
            drive_data=dict(type="list", required=False),
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
                                     f" '{action}'")
            if 'platform_config' not in module.params:
                module.fail_json(msg="'platform_config' is required when 'action' is"
                                     f" '{action}'")
            if 'run_config' not in module.params:
                module.fail_json(msg="'run_config' is required when 'action' is "
                                    f" '{action}'")

            defaults = module.params.get('default_config', {})
            instance_config = module.params["instance_config"]
            platform_config = module.params["platform_config"]
            run_config = module.params["run_config"]

            data, instance_config = prepare_instance_data(instance_config, platform_config, run_config,
                                         defaults)
            module.exit_json(changed=True, instance_data=data,
                             instance_config=instance_config,
                             msg="Instance Data Prepared")

        elif action == "parse_instance":
            if 'instance_config' not in module.params:
                module.fail_json(msg="'instance_config' is required when 'action' is"
                                     f" '{action}'")
            if 'instance_data' not in module.params:
                module.fail_json(msg="'instance_data' is required when 'action' is"
                                     f" '{action}'")

            instance_config = module.params["instance_config"]
            instance_data = module.params["instance_data"]

            instance_config = parse_instance_results(instance_config, instance_data)

            module.exit_json(changed=True, instance_config=instance_config.to_list(),
                             msg="Instance Config Updated from results")

        else:
            raise ValueError(f"Invalid `action` parameter: {action}")

    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}")

    module.exit_json(**result)


if __name__ == "__main__":
    main()

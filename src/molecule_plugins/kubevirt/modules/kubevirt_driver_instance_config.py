from ansible.module_utils.basic import AnsibleModule
import yaml

from molecule_plugins.kubevirt.modules.model.instance_config import InstanceConfig, InstanceConfigList

DOCUMENTATION = '''
---
module: kubevirt_driver_instance_config
short_description: Manage molecule instance configuration files in YAML format for KubeVirt driver
description:
    - This module is used to manage the instance configuration file in YAML format for the KubeVirt driver used in Molecule testing.
    - It allows loading the configuration from a file or saving data to a configuration file. The configuration is structured as an InstanceConfig object and is serialized into YAML format.
    - The module supports check mode, which simulates writing the configuration without making actual changes to the file.
    - It is especially useful for managing configuration files used in the KubeVirt driver for automated testing environments created with Molecule.
author:
    - Cory Close (@cclose)
version_added: "2.10"
requirements:
    - python >= 3.6
    - PyYAML
options:
    action:
        description:
            - The action to perform: either load the configuration or save the configuration.
        type: str
        choices: ['load', 'save']
        required: true
    path:
        description:
            - The path to the YAML file where the instance configuration will be loaded from or saved to.
        type: str
        required: true
    instance_data:
        description:
            - Data to save when performing the 'save' action. This should be instance data from the run.
        type: list
        required: false
        default: None
supports_check_mode: true
notes:
    - In check mode, no files are modified, but it will simulate the changes and set the "changed" status accordingly.
    - Ensure the YAML file structure aligns with the expected format for KubeVirt instance configuration when using the 'save' action.
'''

EXAMPLES = '''
- name: Load instance configuration from file for kubevirt driver
  kubevirt_driver_instance_config:
    action: load
    path: "{{ molecule_instance_config }}"

- name: Save instance configuration to file for KubeVirt driver
  kubevirt_driver_instance_config:
    action: save
    path: "{{ molecule_instance_config }}"
    instance_data: "{{ instances }}"
'''

RETURN = '''
instance_config:
    description: The loaded instance configuration object as a dictionary.
    type: dict
    returned: when action is "load"
instance_yml:
    description: The YAML string representation of the instance configuration.
    type: str
    returned: always
changed:
    description: Indicates whether the configuration file was modified.
    type: bool
    returned: always
msg:
    description: A message indicating the result of the action (e.g., success, failure, check mode).
    type: str
    returned: always
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', choices=['load', 'save'], required=True),
            path=dict(type='str', required=True),
            instance_data=dict(type="list", required=False),
        ),
        supports_check_mode=True
    )

    result = dict(
        changed=False,
    )

    # Extract parameters
    action = module.params['action']
    path = module.params["path"]
    check_mode = module.check_mode

    instance_yml = ''

    try:
        if action == 'load':
            try:
                with open(path, "r") as ic_file:
                    instance_yml = ic_file.read()
                    instance_config = InstanceConfigList.from_yaml(instance_yml)
                    if not instance_config:
                        module.fail_json(msg="Loaded instance configuration is empty or invalid.")
            except FileNotFoundError:
                instance_config = []

            result['instance_config'] = instance_config.to_list() \
                if isinstance(instance_config, InstanceConfigList) else instance_config
            result['instance_yml'] = instance_yml

        elif action == 'save':
            if 'instance_data' in module.params:
                instance_data = InstanceConfigList.from_dict(module.params["instance_data"])
                instance_yml = instance_data.to_yaml()
                result['instance_yml'] = instance_yml
            else:
                module.fail_json(msg="'instance_data' is required when 'action' is 'save'")
            if check_mode:
                # In check mode, we don't actually write, but we simulate the action
                result['changed'] = True  # Indicate that a change would be made
                result['msg'] = f"Check Mode: would have written {path}"
            else:
                with open(path, "w") as ic_file:
                    ic_file.write(instance_yml)
                    result['changed'] = True

    except FileNotFoundError:
        module.fail_json(msg=f"File {path} not found.")
    except PermissionError:
        module.fail_json(msg=f"Permission denied to write to {path}.")
    except yaml.YAMLError as e:
        module.fail_json(msg=f"YAML error: {str(e)}")
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}")

    module.exit_json(**result)


if __name__ == '__main__':
    main()

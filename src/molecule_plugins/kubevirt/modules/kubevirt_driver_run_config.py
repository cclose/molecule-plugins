import os
from os.path import basename

from ansible.module_utils.basic import AnsibleModule
import yaml

from molecule_plugins.kubevirt.modules.model.run_config import RunConfig

DOCUMENTATION = '''
---
module: kubevirt_driver_run_config
short_description: Manage molecule run configuration files in YAML format for KubeVirt driver
description:
    - This module is used to manage the run configuration file in YAML format for the KubeVirt driver used in Molecule testing.
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
            - The path to the YAML file where the run configuration will be loaded from or saved to.
        type: str
        required: true
    run_config:
        description:
            - Data to save when performing the 'save' action. This should be run data from the run.
        type: list
        required: false
        default: None
supports_check_mode: true
notes:
    - In check mode, no files are modified, but it will simulate the changes and set the "changed" status accordingly.
    - Ensure the YAML file structure aligns with the expected format for KubeVirt run configuration when using the 'save' action.
'''

EXAMPLES = '''
- name: Load run configuration from file for KubeVirt driver
  kubevirt_driver_run_config:
    action: load
    path: "{{ run_config_path }}"
  register: run_config

- name: Save run configuration to file for KubeVirt driver
  kubevirt_driver_run_config:
    action: save
    path: "{{ run_config_path }}"
    run_config: "{{ run_config }}"
'''

RETURN = '''
run_config:
    description: The loaded run configuration object as a dictionary.
    type: dict
    returned: when action is "load"
run_yml:
    description: The YAML string representation of the run configuration.
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
            run_config=dict(type="dict", required=False),
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

    run_yml = ''

    try:
        if action == 'load':
            try:
                with open(path, "r") as rc_file:
                    run_yml = rc_file.read()
                    run_config = RunConfig.from_yaml(run_yml)
                    if not run_config:
                        module.fail_json(msg="Loaded run configuration is empty or invalid.")
                    result['changed'] = True  # Indicate that a change would be made
            except FileNotFoundError:
                scene_name = os.getenv("MOLECULE_SCENARIO_NAME")
                molecule_proj = basename(os.getenv("MOLECULE_PROJECT_DIRECTORY"))
                run_prefix = f"m-{molecule_proj}-{scene_name}-"
                run_config = RunConfig.new(molecule_proj, run_prefix, scene_name)
                result['msg'] = "run_config file not found, initialized blank"

            result['run_config'] = run_config.to_dict() \
                if isinstance(run_config, RunConfig) else run_config
            result['run_yml'] = run_yml

        elif action == 'save':
            if 'run_config' in module.params:
                run_config = RunConfig.from_dict(module.params.get("run_config"))
                run_yml = run_config.to_yaml()
                result['run_yml'] = run_yml
            else:
                module.fail_json(msg="'run_config' is required when 'action' is 'save'")
            if check_mode:
                # In check mode, we don't actually write, but we simulate the action
                result['changed'] = True  # Indicate that a change would be made
                result['msg'] = f"Check Mode: would have written {path}"
            else:
                with open(path, "w") as rc_file:
                    rc_file.write(run_yml)
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

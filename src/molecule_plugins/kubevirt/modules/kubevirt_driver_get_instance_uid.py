#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json

def get_instance_uid(molecule_id, instance_data):
    # Loop through instance results and find matches
    # We expect a structure like: item.result.metadata.labels.molecule_id

    for item in instance_data:
        if 'result' in item:
            result = item['result']
            if 'metadata' in result:
                metadata = result['metadata']
                if 'uid' in metadata:
                    item_uid = metadata['uid']
                    if 'labels' in metadata:
                        labels = metadata['labels']
                        if 'molecule_id' in labels:
                            if labels['molecule_id'] == f"{molecule_id}":
                                return item_uid

    return None

def main():
    module = AnsibleModule(
        argument_spec=dict(
            molecule_id=dict(type="str", required=True),
            instance_data=dict(type="list", required=True),
        ),
        supports_check_mode=True
    )

    # Extract parameters
    molecule_id = module.params["molecule_id"]
    instance_data = module.params["instance_data"]

    # Get the UID for the matching instance
    instance_uid = get_instance_uid(molecule_id, instance_data)

    # Return the result
    if instance_uid is None:
        module.fail_json(msg="Failed to get instance uid")
    module.exit_json(changed=False, molecule_id=molecule_id, instance_uid=instance_uid)


if __name__ == '__main__':
    main()

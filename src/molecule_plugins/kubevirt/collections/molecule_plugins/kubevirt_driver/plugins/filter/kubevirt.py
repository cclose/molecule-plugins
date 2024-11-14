import hashlib

class FilterModule(object):
    ''' stuff '''

    def filters(self):
        return {
            'resource_name': self.resource_name
        }

    def generate_unique_suffix(id_string, length=5):
        # Hash the UUID or id_string using SHA256
        hash_object = hashlib.sha256(id_string.encode())
        # Take the first 'length' characters from the hex digest
        return hash_object.hexdigest()[:length]

    def resource_name(self, instance):
        # Check if the instance is a dictionary and contains the required keys
        if not isinstance(instance, dict):
            raise ValueError("Input must be a dictionary.")
        required_keys = ['_run_id', '_dns_name', '_id']
        missing_keys = [key for key in required_keys if key not in instance]
        if missing_keys:
            raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")

        min_name_len = 6
        max_name_len = 63

        run_id = instance['_run_id']
        suffix = self.generate_unique_suffix(instance['_id'])
        boiler_len = len(f"-m{run_id}-{suffix}")
        name_len = max_name_len - boiler_len
        name = instance['_dns_name'][:name_len]

        return f"{name}-m{run_id}-{suffix}"

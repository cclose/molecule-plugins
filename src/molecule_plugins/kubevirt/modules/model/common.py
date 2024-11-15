from dataclasses import asdict, dataclass, fields
from typing import Optional


class DictParserMixin:
    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class DataClassDictValidatorMixin:
    @classmethod
    def validate_dict_keys(cls, data: dict, required_keys: set = None):
        """Compare dict keys with the class attributes."""

        # Get class name
        class_name = cls.__name__
        class_fields = {field.name for field in fields(cls)}
        dict_keys = set(data.keys())

        # if required_keys is set
        # It would be nice to auto-detect optional keys, but this is tricky
        if required_keys is not None:
            missing_keys = required_keys - dict_keys
            if missing_keys:
                raise ValueError(f"[{class_name}] Missing required key(s): "
                                 f"{', '.join(missing_keys)}")

        # Find extra keys
        extra_keys = dict_keys - class_fields
        if extra_keys:
            raise ValueError(f"[{class_name}] Invalid key(s) found: "
                             f"{', '.join(extra_keys)}")

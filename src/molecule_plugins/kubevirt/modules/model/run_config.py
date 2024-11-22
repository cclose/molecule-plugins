import uuid
from dataclasses import dataclass
from typing import Optional
import yaml

from molecule_plugins.kubevirt.modules.model.common import DictParserMixin


@dataclass
class RunConfig(DictParserMixin):
    run_id: str
    run_prefix: str
    molecule_project: str
    scenario_name: str
    ssh_key_path: Optional[str] = None
    ssh_public_key: Optional[str] = None
    ssh_key_token: Optional[str] = "SSH_PUBLIC_KEY"

    # Class constants
    _RUN_ID_LEN: int = 6

    @classmethod
    def from_yaml(cls, yaml_content: str):
        """Load a RunConfig object from a YAML string."""
        data = yaml.safe_load(yaml_content)
        return cls.from_dict(data)

    def to_yaml(self) -> str:
        """Convert the RunConfig objects to a YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False)

    def to_dict(self) -> dict:
        dict = super().to_dict()
        # the magic to_dict mixin won't serialize @properties
        dict["molecule_app_label"] = self.molecule_app_label
        if dict.get("_RUN_ID_LEN"): # no need to serialize a constant
            dict.pop("_RUN_ID_LEN")
        return dict

    @classmethod
    def from_dict(cls, data: dict):
        # this is a calculated field, so drop it
        if data.get("molecule_app_label"):
            data.pop("molecule_app_label")
        return super().from_dict(data)

    @property
    def molecule_app_label(self):
        return f"{self.run_prefix }-{self.run_id}"

    @classmethod
    def new(cls, molecule_project: str, run_prefix: str, scenario_name: str):
        return cls(
            run_id=uuid.uuid4().hex[:cls._RUN_ID_LEN],
            run_prefix=run_prefix,
            molecule_project=molecule_project,
            scenario_name=scenario_name,
        )


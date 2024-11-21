from dataclasses import dataclass
from typing import Optional

from molecule_plugins.kubevirt.modules.model.common import DictParserMixin


@dataclass
class RunConfig(DictParserMixin):
    run_id: str
    run_prefix: str
    ssh_key_path: Optional[str] = None
    ssh_public_key: Optional[str] = None
    ssh_key_token: Optional[str] = "SSH_PUBLIC_KEY"
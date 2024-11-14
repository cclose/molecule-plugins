from dataclasses import dataclass
from typing import List, Optional, Dict

import pytest
from molecule_plugins.kubevirt.modules.model.common import DataClassDictValidatorMixin

@dataclass
class TestClass(DataClassDictValidatorMixin):
    id: int
    name: str

@dataclass
class TestClassWithOptional(DataClassDictValidatorMixin):
    id: int
    name: str
    title: Optional[str]

def test_data_class_dict_validator():
    dict = {
        "id": 2,
        "name": "foo"
    }

    tc = TestClass.validate_dict_keys(dict)
    tco = TestClassWithOptional.validate_dict_keys(dict)

def test_data_class_dict_validator_missing_keys():
    data = {
        "id": 2
    }

    req_keys = {"id", "name"}

    with pytest.raises(ValueError, match=r"\[TestClass\] Missing required key\(s\): name"):
        tc = TestClass.validate_dict_keys(data, req_keys)
    with pytest.raises(ValueError, match=r"\[TestClassWithOptional\] Missing required key\(s\): name"): # noqa: ES501
        tco = TestClassWithOptional.validate_dict_keys(data, req_keys)

def test_data_class_dict_validator_extra_keys():
    data = {
        "id": 2,
        "name": "foo",
        "fish": "Barabarabaracuda"
    }


    req_keys = {"id", "name"}

    with pytest.raises(ValueError, match=r"\[TestClass\] Invalid key\(s\) found: fish"):
        tc = TestClass.validate_dict_keys(data, req_keys)
    with pytest.raises(ValueError, match=r"\[TestClassWithOptional\] Invalid key\(s\) found: fish"):  # noqa: ES501
        tco = TestClassWithOptional.validate_dict_keys(data, req_keys)

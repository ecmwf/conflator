import argparse
from typing import Dict, List, Optional, Union

import pydantic_core
import pytest
from pydantic import validator

from conflator import ConfigModel, Conflator


class DatacubeConfig(ConfigModel):
    axis_config: Dict = {}


class TestLoading:
    def test_loading(self):
        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="polytope", model=DatacubeConfig, argparser=parser)
        datacube_config = conflator.load()
        assert datacube_config.axis_config == {}
        assert datacube_config == DatacubeConfig(axis_config={})

    def test_add_non_existing_field(self):
        with pytest.raises(pydantic_core._pydantic_core.ValidationError):
            parser = argparse.ArgumentParser(allow_abbrev=False)
            conflator = Conflator(app_name="polytope", model=DatacubeConfig, argparser=parser)
            datacube_config = conflator.load()
            datacube_config.new_config = {}

    def test_validator(self):
        class TransformationConfig(ConfigModel):
            # TODO: how to determine according to the str key in the dict, which subtransformation
            # attributes should not be optional anymore...?
            cyclic_options: List[str] = [" "]

            @validator("cyclic_options")
            def check_size(cls, v):
                assert len(v) == 1
                return v

        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="polytope", model=TransformationConfig, argparser=parser, cli=False)
        axis_config = conflator.load()
        assert axis_config == TransformationConfig(cyclic_options=[" "])
        assert axis_config.cyclic_options == [" "]

        with pytest.raises(pydantic_core._pydantic_core.ValidationError):
            axis_config.cyclic_options = ["a", "b"]

    def test_only_optional_config(self):
        class NewConfig(ConfigModel):
            ax: Optional[str] = None
            val: Optional[int] = None

        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="polytope", model=NewConfig, argparser=parser)
        axis_config = conflator.load()
        assert axis_config == NewConfig()

    def test_changing_type(self):
        class IntConfig(ConfigModel):
            i: int = 0

        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="test", model=IntConfig, argparser=parser)
        int_config = conflator.load()
        assert int_config == IntConfig(i=0)
        with pytest.raises(pydantic_core._pydantic_core.ValidationError):
            int_config.i = "i"

    def test_validator_and_nesting(self):
        class SubTransformationConfig(ConfigModel):
            axes: Optional[List[str]] = None

        class TransformationConfig(ConfigModel):
            # TODO: how to determine according to the str key in the dict, which subtransformation
            # attributes should not be optional anymore...?
            cyclic_options: Dict[str, SubTransformationConfig] = {"": SubTransformationConfig()}

            @validator("cyclic_options")
            def check_size(cls, v):
                assert len(v) == 1
                return v

        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="polytope", model=TransformationConfig, argparser=parser)
        axis_config = conflator.load()
        assert axis_config == TransformationConfig()
        assert len(axis_config.cyclic_options) == 1
        assert axis_config.cyclic_options[""].axes is None

    def test_validator_check_dict_keys(self):
        class TransformationConfig(ConfigModel):
            # TODO: how to determine according to the str key in the dict, which subtransformation
            # attributes should not be optional anymore...?
            cyclic_options: Dict[str, int] = {"": 0}

            @validator("cyclic_options")
            def check_keys(cls, v):
                for key in v.keys():
                    assert key in ["", "1", "2"]
                return v

        conflator = Conflator(app_name="polytope", model=TransformationConfig)
        axis_config = conflator.load()
        assert axis_config == TransformationConfig()
        axis_config.cyclic_options["1"] = 2
        assert axis_config == TransformationConfig(cyclic_options={"": 0, "1": 2})
        # TODO: can just add invalid key??
        axis_config.cyclic_options["a"] = 1
        assert axis_config.cyclic_options == {"": 0, "1": 2, "a": 1}
        with pytest.raises(pydantic_core._pydantic_core.ValidationError):
            axis_config.cyclic_options = {"": 0, "1": 2, "a": 1}

    def test_attribute_type_union(self):
        class TransformationConfig(ConfigModel):
            options: Union[str, int] = 1

        conflator = Conflator(app_name="test", model=TransformationConfig)
        axis_config = conflator.load()
        assert axis_config.options == 1
        axis_config.options = "a"
        assert axis_config.options == "a"

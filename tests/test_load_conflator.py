import argparse
from typing import Dict, List, Optional, Union

import pydantic_core
import pytest
from pydantic import validator

from conflator import ConfigModel, Conflator


class Config(ConfigModel):
    dict: Dict = {}


class TestLoading:
    def test_loading(self):
        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="app", model=Config, argparser=parser)
        config = conflator.load()
        assert config.dict == {}
        assert config == Config(dict={})

    def test_add_non_existing_field(self):
        with pytest.raises(pydantic_core._pydantic_core.ValidationError):
            parser = argparse.ArgumentParser(allow_abbrev=False)
            conflator = Conflator(app_name="app", model=Config, argparser=parser)
            config = conflator.load()
            config.new_dict = {}

    def test_validator(self):
        class SubConfig(ConfigModel):
            options: List[str] = [" "]

            @validator("options")
            def check_size(cls, v):
                assert len(v) == 1
                return v

        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(
            app_name="app", model=SubConfig, argparser=parser, cli=False
        )
        config = conflator.load()
        assert config == SubConfig(options=[" "])
        assert config.options == [" "]

        with pytest.raises(pydantic_core._pydantic_core.ValidationError):
            config.options = ["a", "b"]

    def test_only_optional_config(self):
        class NewConfig(ConfigModel):
            string: Optional[str] = None
            val: Optional[int] = None

        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="app", model=NewConfig, argparser=parser)
        config = conflator.load()
        assert config == NewConfig()

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
        class SubConfig(ConfigModel):
            strings: Optional[List[str]] = None

        class Config(ConfigModel):
            options: Dict[str, SubConfig] = {"": SubConfig()}

            @validator("options")
            def check_size(cls, v):
                assert len(v) == 1
                return v

        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="app", model=Config, argparser=parser)
        config = conflator.load()
        assert config == Config()
        assert len(config.options) == 1
        assert config.options[""].strings is None

    def test_validator_check_dict_keys(self):
        class Config(ConfigModel):
            options: Dict[str, int] = {"": 0}

            @validator("options")
            def check_keys(cls, v):
                for key in v.keys():
                    assert key in ["", "1", "2"]
                return v

        conflator = Conflator(app_name="app", model=Config)
        config = conflator.load()
        assert config == Config()
        config.options["1"] = 2
        assert config == Config(options={"": 0, "1": 2})
        # TODO: can just add invalid key??
        config.options["a"] = 1
        assert config.options == {"": 0, "1": 2, "a": 1}
        with pytest.raises(pydantic_core._pydantic_core.ValidationError):
            config.options = {"": 0, "1": 2, "a": 1}

    def test_attribute_type_union(self):
        class Config(ConfigModel):
            options: Union[str, int] = 1

        conflator = Conflator(app_name="test", model=Config)
        config = conflator.load()
        assert config.options == 1
        config.options = "a"
        assert config.options == "a"

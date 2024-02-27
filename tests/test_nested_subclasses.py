from typing import Literal, Union, List

import pytest
import yaml
from pydantic import validator
from pydantic import ConfigDict

from conflator import ConfigModel, Conflator


accepted_axes = ["latitude", "lon", "level"]


class TransformationConfig(ConfigModel):
    model_config = ConfigDict(extra="forbid")
    name: str = ""


class CyclicConfig(TransformationConfig):
    name: Literal["cyclic"]
    range: List[int] = [0, 360]


class MapperConfig(TransformationConfig):
    name: Literal["mapper"]
    type: str = "octahedral"
    resolution: int = 1280
    axes: List[str] = ["latitude", "longitude"]


action_subclasses_union = Union[CyclicConfig, MapperConfig]


class AxisConfig(ConfigModel):
    axis_name: str = ""
    transformations: list[action_subclasses_union]

    @validator("axis_name")
    def check_size(cls, v):
        assert v in accepted_axes
        return v


class Config(ConfigModel):
    config: list[AxisConfig]


def test_nested_subclasses_config():
    config = yaml.safe_load(
            """
    config:
        - axis_name: latitude
          transformations:
            - name: "cyclic"
              range: [0, 1]
        - axis_name: lon
          transformations:
            - name: "cyclic"
              range: [0, 3]
    """
    )
    conflator = Conflator("test-app", Config, cli=False, **config)
    config = conflator.load()
    assert config.config == [AxisConfig(axis_name='latitude',
                                        transformations=[CyclicConfig(name='cyclic', range=[0, 1])]),
                             AxisConfig(axis_name='lon',
                                        transformations=[CyclicConfig(name='cyclic',
                                                                      range=[0, 3])])]


def test_nested_subclasses_config_not_allowed():
    config = yaml.safe_load(
            """
    config:
        - axis_name: latitude
          transformations:
            - name: "cyclic"
              range: [0, 1]
        - axis_name: lev
          transformations:
            - name: "cyclic"
              range: [0, 3]
    """
    )
    with pytest.raises(SystemExit):
        conflator = Conflator("test-app", Config, cli=False, **config)
        config = conflator.load()
        assert config.config == [AxisConfig(axis_name='latitude',
                                            transformations=[CyclicConfig(name='cyclic', range=[0, 1])]),
                                 AxisConfig(axis_name='level',
                                            transformations=[CyclicConfig(name='cyclic',
                                                                          range=[0, 3])])]

from dataclasses import dataclass, field
from typing import Literal, Union

import pytest
import yaml
from annotated_types import Annotated
from pydantic import ConfigDict, Field

from conflator import ConfigModel, Conflator


class Action(ConfigModel):
    model_config = ConfigDict(extra="forbid")
    model_config = ConfigDict(extra="forbid")
    name: str


class Source(Action):
    "Produces messages"
    name: Literal["Source"]
    start_from: str


class Process(Action):
    "Processes messages"
    name: Literal["Process"]
    should_flub_widgets: bool


class Sink(Action):
    "Consumes messages"
    name: Literal["Sink"]
    emit_aviso_notification: bool


@dataclass
class Subclasses:
    """Get all the subclasses for given class
    returns {name : class}
    deduplicated by name
    cached
    """

    cache: dict = field(default_factory=dict)

    def get(self, target):
        try:
            return self.cache[target.__name__]
        except KeyError:
            # Deduplicate classes by __name__
            deduped = list(
                {subcls.__name__: subcls for subcls in target.__subclasses__()}.values()
            )
            subclasses = {target.__name__: target} | {
                k: v for subcls in deduped for k, v in self.get(subcls).items()
            }
            subclasses[target.__name__] = target
            self.cache[target.__name__] = subclasses
            return subclasses


# Get all the subclasses of  Action and remove Action itself
action_subclasses = tuple(
    set(Subclasses().get(Action).values())
    - set(
        [
            Action,
        ]
    )
)
action_subclasses = tuple(
    set(Subclasses().get(Action).values())
    - set(
        [
            Action,
        ]
    )
)

# Constuct a union type out of the subclasses
# Field(discriminator="name") tells pydantic to look at the name
# field to decide what type of the union to attempt to parse
action_subclasses_union = Annotated[
    Union[action_subclasses], Field(discriminator="name")
]


class Config(ConfigModel):
    actions: list[action_subclasses_union] = Field(discriminator="name")

    actions: list[action_subclasses_union] = Field(discriminator="name")


def test_subclasses():
    config = yaml.safe_load(
        """
actions:
    - name: "Source"
      start_from: 01031997
    #   should_flub_widgets: True # extra key

    - name: Process
      should_flub_widgets: True

    - name: Sink
      emit_aviso_notification: False
"""
    )
    conflator = Conflator("test-app", Config, cli=False, **config)
    config = conflator.load()

    assert config.actions[0].name == "Source"


def test_subclasses_extra_key():
    with pytest.raises(SystemExit):
        config = yaml.safe_load(
            """
    actions:
        - name: "Source"
          start_from: 01031997
          should_flub_widgets: True # extra key

        - name: Process
          should_flub_widgets: True

        - name: Sink
          emit_aviso_notification: False
    """
        )
        conflator = Conflator("test-app", Config, cli=False, **config)
        config = conflator.load()

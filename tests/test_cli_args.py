from unittest.mock import patch
from typing import Any

from annotated_types import Annotated
from pydantic import Field, model_validator, create_model, ConfigDict

from conflator import CLIArg, ConfigModel, Conflator, EnvVar


class NestedConfig(ConfigModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    nested_field: Annotated[str, CLIArg("--nested")] = "default_value"


class ConfigWithCLI(ConfigModel):
    arg1: NestedConfig = NestedConfig()


class InheritedConfig(ConfigWithCLI):
    pass


class Config(ConfigModel):
    test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
    test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"
    nested_config: NestedConfig = NestedConfig()


def test_cli_argument_override():
    test_args = ["--test-email", "cli@example.com"]
    with patch("sys.argv", ["test_script.py"] + test_args):
        conflator = Conflator("polytope", Config, nested={})
        config = conflator.load()
        assert config.test_email == "cli@example.com"


def test_inherited_cli_arg():
    conflator = Conflator("test", InheritedConfig)
    cli_args = set()
    for m in Conflator._find_models(conflator.model):
        cli_args |= Conflator._get_cli_args(m, cli_args)
    assert len(cli_args) == 1

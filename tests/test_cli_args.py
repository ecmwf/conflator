from unittest.mock import patch
import pytest
from conflate import CLIArg, Conflater, EnvVar, ConfigModel
from annotated_types import Annotated
from pydantic import Field

class NestedConfig(ConfigModel):
    nested_field: str = "default_value"

class Config(ConfigModel):
    test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
    test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"
    nested_config: NestedConfig = NestedConfig()

def test_cli_argument_override():
    test_args = ["--test-email", "cli@example.com"]
    with patch("sys.argv", ["test_script.py"] + test_args):
        conflater = Conflater("polytope", Config, nested={})
        config = conflater.load()

        assert config.test_email == "cli@example.com"

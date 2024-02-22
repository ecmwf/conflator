from unittest.mock import patch

from annotated_types import Annotated
from pydantic import Field

from conflator import CLIArg, ConfigModel, Conflator, EnvVar


class NestedConfig(ConfigModel):
    nested_field: str = "default_value"


class Config(ConfigModel):
    test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
    test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"
    nested_config: NestedConfig = NestedConfig()


def test_envvar_initialization():
    env_var = EnvVar("TEST_VAR")
    assert env_var.name == "TEST_VAR"


def test_environment_variable_override(monkeypatch):
    monkeypatch.setenv("APPNAME_TEST_EMAIL", "env@example.com")
    monkeypatch.setenv("APPNAME_TEST_KEY", "env_key")

    with patch("sys.argv", ["test_script.py"]):
        conflator = Conflator("appname", Config, nested={})
        config = conflator.load()

    assert config.test_email == "env@example.com"
    assert config.test_key == "env_key"

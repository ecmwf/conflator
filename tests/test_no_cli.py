from annotated_types import Annotated
from pydantic import Field

from conflator import CLIArg, ConfigModel, Conflator, EnvVar


class Config(ConfigModel):
    test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
    test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"


def test_no_cli():
    conflator = Conflator("polytope", Config, cli=False)
    conflator = Conflator("polytope", Config, cli=False)
    config = conflator.load()
    print(config)

from unittest.mock import patch
import pytest
from conflator import CLIArg, Conflator, EnvVar, ConfigModel
from annotated_types import Annotated
from pydantic import Field

class Config(ConfigModel):
    test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
    test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"

def test_no_cli():
    conflator = Conflator("polytope", Config, cli = False)
    config = conflator.load()

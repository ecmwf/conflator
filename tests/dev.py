from typing import Annotated, Tuple, Union

from pydantic import Field

from conflator import CLIArg, ConfigModel, Conflator, EnvVar


class DoubleNested2(ConfigModel):
    doubletest: Annotated[str, EnvVar("dt"), Field(required=True)] = "foooo"


class DoubleNested(ConfigModel):
    doubletest: Annotated[str, EnvVar("dt")] = "fooooo"


class NestedConfig(ConfigModel):
    test: str = "foo"
    double_nested: DoubleNested = DoubleNested(doubletest="bar")
    double_nested2: DoubleNested2 = DoubleNested2()


class Config(ConfigModel):
    user_email: Annotated[str, Field(), EnvVar("USER_EMAIL"), CLIArg("--user-email")] = "foo"
    user_key: Annotated[str, Field(description="Your API Key"), EnvVar("XYZ")] = "xyz"
    url: str = "http://example.com"
    secure: bool = Field(False)
    nested: NestedConfig = None
    # nested_list : List[List[NestedConfig]] = None


c = Conflator("polytope", Config, nested={}).load()

print(Conflator("polytope", Config, nested={}).schema())


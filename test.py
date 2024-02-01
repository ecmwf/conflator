from typing import Annotated, Tuple, Union

from pydantic import (
    Field,
)

from conflate import CLIArg, ConfigModel, Conflater, EnvVar


def loc_to_dot_sep(loc: Tuple[Union[str, int], ...]) -> str:
    path = ""
    for i, x in enumerate(loc):
        if isinstance(x, str):
            if i > 0:
                path += " > "
            path += x
        elif isinstance(x, int):
            path += f"[{x}]"
        else:
            raise TypeError("Unexpected type")
    return path


class DoubleNested2(ConfigModel):
    doubletest: Annotated[str, EnvVar("dt"), Field(required=True)] = "foooo"


class DoubleNested(ConfigModel):
    doubletest: Annotated[str, EnvVar("dt")] = "fooooo"


class NestedConfig(ConfigModel):
    test: str = "foo"
    double_nested: DoubleNested = DoubleNested(
        doubletest="bar"
    )  # This isn't good, it calls the wrap function immediately
    # and then interpolating of environment happens too early
    double_nested2: DoubleNested2 = DoubleNested2()
    # test_miss: str = "bar"


class Config(ConfigModel):
    user_email: Annotated[str, Field(), EnvVar("USER_EMAIL"), CLIArg("--user-email")] = "foo"
    user_key: Annotated[str, Field(description="Your API Key"), EnvVar("XYZ")] = "xyz"
    url: str = "http://example.com"
    secure: bool = Field(False)
    nested: NestedConfig = None
    # nested_list : List[List[NestedConfig]] = None


print("END DEF")

c = Conflater("polytope", Config, nested={}).load()


print("doing...")
print(c.url)
c.url = "hello"
print(c.url)


# Maybe dynamic CLI is too much... CLI are which change based on the values of config already provided is tricky


# print(c)

# result = Conflater("polytope", Config, cli=False).load()


# print(result)

from typing import List

from annotated_types import Annotated
from pydantic import Field

from conflate import CLIArg, ConfigModel, Conflater, EnvVar


class NestedConfig(ConfigModel):
    # Can be provided by environment <APP>_TEST, environment variable is given explicitly
    test: Annotated[str, EnvVar("TEST")]

    # Can be provided by environment <APP>_TEST2
    # ... but is that what we want? Should it be <APP>_DEEPER_TEST2? or <APP>_NESTEDCONFIG_TEST2 (using class name)?
    test2: Annotated[str, EnvVar()]

    # And what about the CLIArg? Should it be --deeper.test2 or --test2 or ?
    test2: Annotated[str, EnvVar(), CLIArg()]


class Config(ConfigModel):
    # Required, but no default. Can be provided by environment <APP>_USER_EMAIL or CLI --user-email
    # Pydantic Field can be used to add descriptions for the config schema and CLI help
    user_email: Annotated[
        str,
        EnvVar("USER_EMAIL"),
        CLIArg("user-email"),
        Field(description="Your email address"),
    ]

    # Required, but no default. Can be provided by CLI --user-key
    user_key: Annotated[str, EnvVar(), CLIArg("user-key")]

    # Should CLIArg assume the name as the field name? --foo?
    foo: Annotated[str, CLIArg()] = "bar"

    # Can only be overriden by config
    url: str = "polytope.ecmwf.int"

    # Can only be overriden by config
    secure: bool = True

    deeper: NestedConfig = NestedConfig()

    # Gets complicated quickly...
    deeperlist: List[NestedConfig] = [NestedConfig()]


# Will error and display CLI help because user_email and user_key are undefined
conf = Conflater("polytope", Config, cli=True).load()

# Will not error, everything is defined. CLI help can still be displayed with "-h" or "--help"
conf = Conflater("polytope", Config, cli=True, user_email="hello", user_key="world").load()

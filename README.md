![conflator logo](docs/conflator.png)

# Conflator

Conflator is a configuration-handling library for Python. It is designed to simplify the handling of configuration from multiple sources, such as environment variables, command line arguments, and configuration files. As an application or library developer, you specify your configuration schema with a Pydantic model, and conflator will handle the rest.

## Installation

Conflator is available on PyPI:

```bash
pip install conflator
```

Or using poetry:

```bash
poetry add conflator
```

## Usage

1. **Define Your Configuration Model**: Begin by defining your configuration schema using Pydantic models. Annotate your model fields with EnvVar and CLIArg for environment variable and command-line argument support, respectively.

```python
from pydantic import BaseModel, Field
from conflate import EnvVar, CLIArg, ConfigModel

# Inherit from ConfigModel instead of pydantic's BaseModel
class AppConfig(ConfigModel):

    # Simple type hinting
    db_name: str = "my_app"

    # Using pydantic's Field class
    db_host: str = Field(default="localhost", description="Database host")

    # Using annotations
    db_timeout: int = Annotation(10, Field(description="Database timeout")))

    # Using conflate's EnvVar and CLIArg annotations
    db_port: Annotated[int, EnvVar("DB_PORT"), CLIArg("--db-port")] = 5432

    # Using conflate's EnvVar and CLIArg annotations with pydantic's Field class
    db_user: Annotated[str, EnvVar("DB_USER"), CLIArg("--db-user")] = Field(description="Database user")

    # You can nest ConfigModels as usual
    # more_config: Annotated[MoreConfig, EnvVar("MORE_CONFIG"), CLIArg("--more-config")] = DbConfig()
```

2. **Initialize Conflater**: Create an instance of the Conflater class, passing your application's name and the configuration model.

```python
from conflate import Conflater

config = Conflater(app_name="my_app", model=AppConfig).load()
```

3. **Access Configuration**: Use the loaded configuration throughout your application.
```python
print(f"Database Host: {config.db_host}")
print(f"Database Port: {config.db_port}")
```

4. **Environment Variables and CLI Arguments**: Conflator automatically maps environment variables and CLI arguments to your configuration model. For example, the db_port field can be set using the MY_APP_DB_PORT environment variable or the --db-port CLI argument.


## Limitations

* CLI arguments and environment variables are defined per model type, not per model instance. This means that you cannot have different CLI arguments or environment variables for different instances of the same model. Some support for this may be added in the future.

* Including ConfigModel's from other packages, to nest their configuration with yours, is possible. However, there is no way to resolve conflicts between CLI arguments and environment variable naming between two different config schemas. Some support for this may be added in the future.
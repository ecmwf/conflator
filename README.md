> [!WARNING]
> This project is under development and not yet feature complete or tested.


![conflator logo](docs/conflator.png)

> [!WARNING]
> This project is BETA and will be experimental for the forseable future. Interfaces and functionality are likely to change, and the project itself may be scrapped. DO NOT use this software in any project/software that is operational.

Conflator is a configuration-handling library for Python. It is designed to simplify the handling of configuration from multiple sources, such as environment variables, command line arguments, and configuration files. As an application or library developer, you specify your configuration schema with a Pydantic model, and conflator will handle the rest.

Conflator loads configuration in the following order:

1. Default values specified in the Pydantic model
2. System-wide configuration in /etc/appname/config.json (and yaml)
3. User configuration in ~/.appname.json (and yaml)
4. Additional configuration files and values provided as command line args (e.g. `-f filename` or `--set value.deeper=foo`)
4. Environment variables
5. Command-line arguments
6. Dictionaries passed to the load method

...and then validates the merged configuration against the Pydantic model.

<!-- > Conflate (/kənˈfleɪt/): combine (two or more sets of information, texts, ideas, etc.) into one. -->

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

1. **Define Your Configuration Model**: Begin by defining your configuration schema using Pydantic models. Annotate your model fields with `EnvVar` and `CLIArg` for environment variable and command-line argument support, respectively.

```python
from pydantic import Field
from conflator import EnvVar, CLIArg, ConfigModel
from annotations import Annotated

class AppConfig(ConfigModel):

    host: str = "localhost"
    port: Annotated[int, EnvVar("PORT"), CLIArg("--port")] = 5432
    user: Annotated[str, EnvVar("USER"), CLIArg("--user"), Field(description="Your username")] = "foo"
```

2. **Initialize Conflator**: Create an instance of the Conflator class, passing your application's name and the configuration model.

```python
from conflator import Conflator

config = Conflator(app_name="my_app", model=AppConfig).load()
```

3. **Access Configuration**: Use the loaded configuration throughout your application, knowing that the configuration has been fully validated.
```python
print(f"User: {config.user}")
```
Try setting MY_APP_USER in the environment to see the value change, or use the `--user` flag to override the value.

## Advanced Usage

### Configuration layering for different deployments

```bash
your-app -f ./config/base.yaml -f ./config/production.yaml
```

### Nested config just works
```python
from annotations import Annotated
from conflator import EnvVar, CLIArg, ConfigModel

class DeeperConfig(ConfigModel):
    nested: Annnotated[str, EnvVar("NESTED"), CLIArg("--nested")] = "default"

class Config(ConfigModel):
    host: str = "localhost"
    port: int = 543
    deeper: DeeperConfig = DeeperConfig()
```

### Generate the JSON schema for your configuration
```bash
config = Conflator(app_name="my_app", model=AppConfig).schema() # uses pydantic's schema method behind the scenes
```

## Limitations

* CLI arguments and environment variables are defined per model type, not per model instance. This means that you cannot have different CLI arguments or environment variables for different instances of the same model. Some support for this may be added in the future.

* Including ConfigModel's from other packages, to nest their configuration with yours, is possible. However, there is no way to resolve conflicts between CLI arguments and environment variable naming between two different config schemas. Some support for this may be added in the future.

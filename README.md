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

> Conflate (/kənˈfleɪt/): combine (two or more sets of information, texts, ideas, etc.) into one.

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
from conflate import EnvVar, CLIArg, ConfigModel

class AppConfig(ConfigModel):

    host: str = "localhost"
    port: Annotated[int, EnvVar("PORT"), CLIArg("--port")] = 5432
    user: Annotated[str, EnvVar("USER"), CLIArg("--user"), Field(description="Your username")]

    # You can nest ConfigModels as usual, and use the `EnvVar` and `CLIArg` annotations on nested models
    # more_config: Annotated[MoreConfig, EnvVar("MORE_CONFIG"), CLIArg("--more-config")] = MoreConfig()
```

2. **Initialize Conflater**: Create an instance of the Conflater class, passing your application's name and the configuration model.

```python
from conflate import Conflater

config = Conflater(app_name="my_app", model=AppConfig).load()
```

3. **Access Configuration**: Use the loaded configuration throughout your application, knowing that the configuration has been fully validated.
```python
print(f"Host: {config.host}")
print(f"Port: {config.port}")
```

## Advanced Usage

### Configuration layering for different deployments

```bash
your-app -f ./config/base.yaml -f ./config/production.yaml
```

### Generate the JSON schema for your configuration
```bash
config = Conflater(app_name="my_app", model=AppConfig).schema() # uses pydantic's schema method behind the scenes
```

## Limitations

* CLI arguments and environment variables are defined per model type, not per model instance. This means that you cannot have different CLI arguments or environment variables for different instances of the same model. Some support for this may be added in the future.

* Including ConfigModel's from other packages, to nest their configuration with yours, is possible. However, there is no way to resolve conflicts between CLI arguments and environment variable naming between two different config schemas. Some support for this may be added in the future.
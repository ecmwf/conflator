import argparse
from collections import defaultdict
from typing import Dict, Any, List, Union, Tuple
from enum import Enum
from pydantic import BaseModel, ValidationError, model_validator
from pydantic_core import PydanticUndefined
from pydantic_core import PydanticCustomError
from pathlib import Path
from rich_argparse import RichHelpFormatter
import json
import os

from rich import print as rprint
from rich.tree import Tree as rtree


from pydantic.functional_validators import BeforeValidator, WrapValidator

class ConfigError(ValueError):
    def __init__(self, extra=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra = None

class CLIArg:
    def __init__(self, long_name: str = None, short_name: str = None):
        self.long_name = long_name
        self.short_name = short_name

class EnvVar:
    def __init__(self, name: str = None):
        # print(f"ENV VAR {name} INIT")
        self.name = name


class ConfigModel(BaseModel, revalidate_instances='always', validate_assignment=True, validate_default=True):



    @model_validator(mode='wrap')
    @classmethod
    def wrap_root(cls, unvalidated, handler, info):

        if type(info.context) == ParseContext and info.context.mode == ParseMode.INITIALISE:
            return cls._conflater_initialise(unvalidated, handler, info.context)
    
        if type(info.context) == ParseContext and info.context.mode == ParseMode.VALIDATE:
            return cls._conflater_validate(unvalidated, handler, info.context)
        
        return handler(unvalidated)


        # rprint(f"WRAP ROOT in cls {cls} with unvalidated {unvalidated}")
        # rprint(f"UNVALIDATED: {unvalidated}")
        # # rprint(f"INFO: {info}")
        # # rprint(f"HANDLER: {handler}")
        # # rprint(f"Type of unvalidated: {type(unvalidated)}")

        # if isinstance(unvalidated, cls):
        #     rprint("Input is already a model")
        #     return handler(unvalidated)
        
        # if unvalidated is None:
        #     rprint("Nothing to validate")
        #     return handler(unvalidated)
        
        # # Interpolate environment variables
        # for k,v in unvalidated.items():
        #     if k in cls.model_fields:
        #         other_annotations = cls.model_fields[k].metadata
        #         for annotation in other_annotations:
        #             if isinstance(annotation, EnvVar):
        #                 unvalidated[k] = os.environ.get(annotation.name, v)
        #             if isinstance(annotation, CLIArg):
        #                 # Not sure how to handle this yet
        #                 pass

        # # Could catch errors here, and check them later against argparser?

        # try:
        #     validated = handler(unvalidated)
        # except ValidationError as e:
        #     e.add_note("note")
        #     raise e
        #     raise PydanticCustomError(type(e), "", {'test': 'test'})
        
        # return validated
    
    @classmethod
    def _conflater_initialise(cls, unvalidated, handler, context):
        
        # Creates a mapping of 
        for k,v in cls.model_fields.items():
            cli_args = [m for m in v.metadata if type(m) == CLIArg]
            for ca in cli_args:
                name = ca.long_name or k
                context.CLIArgs[name].append(ca)
        
        rprint("HANDLER")
        rprint(handler)

        return handler(unvalidated)

    @classmethod
    def _conflater_validate(self, unvalidated, handler, context):
        return handler(unvalidated)


    # @classmethod
    # def conflate(cls, app_name=None, cli=True, **kwargs):

class ParseMode(Enum):
    INITIALISE = 1
    VALIDATE   = 2

class ParseContext():
    def __init__(self):
        self.mode = ParseMode.INITIALISE
        self.CLIArgs : Dict[str, List[CLIArg]] = defaultdict(list)

class Conflater():

    def __init__(
            self,
            app_name,
            model: type[BaseModel],
            cli=True,
            argparser : argparse.ArgumentParser = None,
            **overrides: Dict[str, Any]
    ):
        self.app_name = app_name
        self.model = model
        self.cli = cli
        self.parser = argparser
        self.overrides = overrides

        self.config_files = [
            Path()/"etc"/self.app_name/"config.json",
            Path.home()/f".{self.app_name}apirc"
        ]
    
    def load(self) -> BaseModel:
        
        self.loaded_config = {}
        
        # Update configuration from files
        self._update_from_files()

        # # Overrides
        # self.loaded_config.update(self.overrides)

        # Create the model, catching all errors
        parse_context = ParseContext()
        parse_context.mode = ParseMode.INITIALISE


        try:
            result = self.model.model_validate(self.loaded_config, context=parse_context)
        except ValidationError as e:
            pass            

        
        
        for k,v in parse_context.CLIArgs.items():
            rprint(k, v)
            # self.parser.add_argument(f"--{k}", help="test")
            # output = rtree(f"[red]Configuration errors: {e.error_count()}[/red]")

            # for e in e.errors():
            #     rprint(e)
            #     output.add(f"[red]{e['msg'].upper()}:[/red][cyan] {self._loc_to_dot_sep(e['loc'])}[/cyan]")
            #     # self.parser.add_argument(f"--{self._loc_to_dot_sep(e['loc']).upper()}", help=e["msg"])

            # rprint(output)

            # # raise ConfigError(extra=e)
        

        # # Apply overrides

        return result
    
    def _merge(self, b, path=None):

        a = self.loaded_config
        # b = copy.deepcopy(b)

        if path is None:
            path = []

        if not isinstance(b, dict):
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            self.loaded_config = b

        for key in b:
            if key in a:
                if b[key] is None:
                    del a[key]
                elif isinstance(a[key], dict) and isinstance(b[key], dict):
                    a[key] = self._merge(a[key], b[key], path + [str(key)])
                elif isinstance(a[key], list) and isinstance(b[key], list):
                    a[key] = a[key] + b[key]
                elif a[key] == b[key]:
                    pass
                else:
                    a[key] = b[key]
            else:
                if b[key] is not None:
                    a[key] = b[key]
        
    def _update_from_files(self) -> Dict:
    
        def from_file(path: Path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                return {}
            
        # Try to read from files

        for cf in self.config_files:
            self._merge(from_file(cf))


    def _update_from_env(self) -> Dict:

        # Try to read from environment variables (case insensitive)
        env_vars = {k.upper(): v for k, v in os.environ.items()}
        for k,v in self.model.model_fields.items():
            key = f"{self.app_name.upper()}_{(v.alias or k).upper()}"
            if key in env_vars:
                self.loaded_config[v.alias] = env_vars[key]
        
    def _update_from_cli_args(self):

        if not self.parser:
            self.parser = argparse.ArgumentParser(
                    description=f"""
                        All arguments can be overriden with {self.app_name.upper()}_ARG.\n\n

                        They can also be set in JSON files: /etc/{self.app_name}/config.json and ~/.{self.app_name}apirc
                    """,
                    formatter_class=RichHelpFormatter
                )
        # Add arguments based on Pydantic model fields
        for field_name, field in self.model.model_fields.items():

            if field_name in self.loaded_config:
                default = self.loaded_config[field_name]
                help = f"{field.description or ''} (found: {self.loaded_config[field_name]})"
            else:
                default = field.default
                help = field.description
            
            self.parser.add_argument(
                f"--{field_name}",
                type=str,
                required=field.is_required and field.default is PydanticUndefined and field_name not in self.loaded_config,
                default=default,
                help=help
            )

        args = self.parser.parse_args()
        self.loaded_config.update(args.__dict__)
    
    @staticmethod
    def _loc_to_dot_sep(loc: Tuple[Union[str, int], ...]) -> str:
        path = ''
        for i, x in enumerate(loc):
            if isinstance(x, str):
                if i > 0:
                    path += ' > '
                path += x
            elif isinstance(x, int):
                path += f'[{x}]'
            else:
                raise TypeError('Unexpected type')
        return path
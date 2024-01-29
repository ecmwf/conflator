import argparse
from pydantic import BaseModel, Field
from typing import Dict
from pydantic import BaseModel
from pydantic_core import PydanticUndefined
from pathlib import Path
from rich_argparse import RichHelpFormatter
import json
import os
import copy



class Conflater():

    def __init__(
            self,
            app_name,
            model: type[BaseModel],
            cli=True,
            argparser : argparse.ArgumentParser = None,
            *overrides: Dict
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

        # Update configuration from environment variables
        self._update_from_env()

        # Update configuration from command-line arguments, and create CLI help text
        if self.cli or self.argparser:
            self._update_from_cli_args()

        # Apply overrides
        for override in self.overrides:
            self.loaded_config.update(override)

        return self.model(**self.loaded_config)
    
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
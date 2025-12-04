from typing import Annotated
from unittest.mock import patch

from pydantic import Field

from conflator import CLIArg, ConfigModel, Conflator, EnvVar


class TestLoading:
    def test_find_models(self):
        class Config(ConfigModel):
            test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
            test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"

        found_models = Conflator._find_models(Config)
        for model in found_models:
            assert model == Config

        class NestedConfig(ConfigModel):
            nested_key: int = 0

        class NewConfig(ConfigModel):
            first_key: int = 1
            nested: NestedConfig = NestedConfig()

        found_models = Conflator._find_models(NewConfig)
        assert len(found_models) == 2
        for model in found_models:
            assert model in [NewConfig, NestedConfig]

    def test_get_cli_args(self):
        class Config(ConfigModel):
            test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
            test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"

        test_args = ["--test-email", "cli@example.com"]
        with patch("sys.argv", ["test_script.py"] + test_args):
            conflator = Conflator("polytope", Config)
            config = conflator.load()
            cli_args = Conflator._get_cli_args(config)
            assert len(cli_args) == 1
            for arg in cli_args:
                assert arg.argparse_key == "test_email"
                assert arg.description == ""
                assert arg.args == ("--test-email",)

        class NewConfig(ConfigModel):
            test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
            test_key: Annotated[
                str,
                Field(description="Test API Key"),
                EnvVar("TEST_KEY"),
                CLIArg("--test-key"),
            ] = "default_key"

        test_args = ["--test-key", "key_example"]
        with patch("sys.argv", ["test_script.py"] + test_args):
            conflator = Conflator("polytope", NewConfig)
            config = conflator.load()
            cli_args = Conflator._get_cli_args(config)
            assert len(cli_args) == 2
            for arg in cli_args:
                assert arg.argparse_key in ["test_email", "test_key"]
                assert arg.description in ["Test API Key", ""]
                if arg.argparse_key == "test_email":
                    assert arg.args == ("--test-email",)
                else:
                    assert arg.args == ("--test-key",)

    def test_schema(self, monkeypatch):
        class Config(ConfigModel):
            test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
            test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"

        monkeypatch.setenv("APPNAME_TEST_KEY", "env_key")

        with patch("sys.argv", ["test_script.py"]):
            conflator = Conflator("appname", Config)
            config = conflator.load()
            assert config.test_key == "env_key"
            assert conflator.schema() == {
                "properties": {
                    "test_email": {
                        "default": "default@example.com",
                        "title": "Test Email",
                        "type": "string",
                    },
                    "test_key": {
                        "default": "default_key",
                        "description": "Test API Key",
                        "title": "Test Key",
                        "type": "string",
                    },
                },
                "title": "Config",
                "type": "object",
            }

        class NestedConfig(ConfigModel):
            key: str = "test"

        class NewConfig(ConfigModel):
            test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
            test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"
            nested_key: NestedConfig = NestedConfig()

        monkeypatch.setenv("APPNAME_TEST_KEY", "env_key")

        with patch("sys.argv", ["test_script.py"]):
            conflator = Conflator("appname", NewConfig)
            config = conflator.load()
            assert config.test_key == "env_key"
            assert conflator.schema() == {
                "$defs": {
                    "NestedConfig": {
                        "properties": {"key": {"default": "test", "title": "Key", "type": "string"}},
                        "title": "NestedConfig",
                        "type": "object",
                    }
                },
                "properties": {
                    "test_email": {
                        "default": "default@example.com",
                        "title": "Test Email",
                        "type": "string",
                    },
                    "test_key": {
                        "default": "default_key",
                        "description": "Test API Key",
                        "title": "Test Key",
                        "type": "string",
                    },
                    "nested_key": {
                        "$ref": "#/$defs/NestedConfig",
                        "default": {"key": "test"},
                    },
                },
                "title": "NewConfig",
                "type": "object",
            }

    def test_dot_path_to_nested_dict(self):
        path = "test-0.test-1.test-2"
        assert Conflator._dot_path_to_nested_dict(path, 2, False) == {"test-0": {"test-1": {"test-2": 2}}}
        assert Conflator._dot_path_to_nested_dict(path, 2, True) == {"test_0": {"test_1": {"test_2": 2}}}

    def test_merge(self, monkeypatch):
        class Config(ConfigModel):
            test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
            test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"

        conflator = Conflator("appname", Config)

        monkeypatch.setenv("APPNAME_TEST_KEY", "env_key_2")

        with patch("sys.argv", ["test_script.py"]):
            conflator.load()
            conflator._update_from_env()
        assert conflator.loaded_config == {"test_key": "env_key_2"}

        Conflator._merge(conflator.loaded_config, {"test_email": "new_default@example.com"})
        assert conflator.loaded_config == {
            "test_key": "env_key_2",
            "test_email": "new_default@example.com",
        }

        Conflator._merge(conflator.loaded_config, {"test_key": "env_key_3"})
        assert conflator.loaded_config == {
            "test_key": "env_key_3",
            "test_email": "new_default@example.com",
        }

        Conflator._merge(conflator.loaded_config, {"test_key": None})
        assert conflator.loaded_config == {"test_email": "new_default@example.com"}

        Conflator._merge(conflator.loaded_config, {"test_key": [1, 2]})
        assert conflator.loaded_config == {
            "test_email": "new_default@example.com",
            "test_key": [1, 2],
        }

        Conflator._merge(conflator.loaded_config, {"test_key": [3, 4]})
        assert conflator.loaded_config == {
            "test_email": "new_default@example.com",
            "test_key": [1, 2, 3, 4],
        }

        Conflator._merge(conflator.loaded_config, {"test_key": None})
        assert conflator.loaded_config == {"test_email": "new_default@example.com"}

        Conflator._merge(conflator.loaded_config, {"test_key": {"test": 1}})
        assert conflator.loaded_config == {
            "test_email": "new_default@example.com",
            "test_key": {"test": 1},
        }

        Conflator._merge(conflator.loaded_config, {"test_key": [2]})
        assert conflator.loaded_config == {
            "test_email": "new_default@example.com",
            "test_key": [2],
        }

        # TODO: implement this...
        Conflator._merge(conflator.loaded_config, {"test_key": {"test_1": 2}})
        assert conflator.loaded_config == {
            "test_email": "new_default@example.com",
            "test_key": {"test_1": 2},
        }

        Conflator._merge(conflator.loaded_config, {"new_test_key": {"test_1": 2}})
        assert conflator.loaded_config == {
            "test_email": "new_default@example.com",
            "test_key": {"test_1": 2},
            "new_test_key": {"test_1": 2},
        }

        conflator.loaded_config = [1]
        result = Conflator._merge(conflator.loaded_config, [2])
        assert result == [1, 2]

    def test_update_from_env(self, monkeypatch):
        class Config(ConfigModel):
            test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
            test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"

        monkeypatch.setenv("APPNAME_TEST_KEY", "env_key")

        with patch("sys.argv", ["test_script.py"]):
            conflator = Conflator("appname", Config)
            config = conflator.load()
            assert config.test_key == "env_key"

        monkeypatch.setenv("APPNAME_TEST_KEY", "env_key_2")

        with patch("sys.argv", ["test_script.py"]):
            conflator._update_from_env()
            assert conflator.loaded_config["test_key"] == "env_key_2"

    def test_update_from_cli_args(self):
        class Config(ConfigModel):
            test_email: Annotated[str, Field(), EnvVar("TEST_EMAIL"), CLIArg("--test-email")] = "default@example.com"
            test_key: Annotated[str, Field(description="Test API Key"), EnvVar("TEST_KEY")] = "default_key"

        test_args = ["--test-email", "cli@example.com"]
        with patch("sys.argv", ["test_script.py"] + test_args):
            conflator = Conflator("polytope", Config)
            config = conflator.load()
            assert config.test_email == "cli@example.com"
        new_test_args = ["--test-email", "new_cli@example.com"]
        with patch("sys.argv", ["test_script.py"] + new_test_args):
            conflator._update_from_cli_args()
            assert conflator.loaded_config["test_email"] == "new_cli@example.com"

    def test_loc_to_dot_sep(self):
        test_cases = [
            ((1, "a", 2), "[1] > a[2]"),
            (("a", "b", "c"), "a > b > c"),
            ((1, "a", "b", "c", 2), "[1] > a > b > c[2]"),
            ((1, 2, 3, 4), "[1][2][3][4]"),
            (("a", 1, 2, "b"), "a[1][2] > b"),
        ]
        for tuple, expected in test_cases:
            result = Conflator._loc_to_dot_sep(tuple)
            assert result == expected

from typing import Dict

from conflator import ConfigModel, Conflator

import argparse


class DatacubeConfig(ConfigModel):
    axis_config: Dict = {}


class TestLoading:

    def test_loading(self):
        parser = argparse.ArgumentParser(allow_abbrev=False)
        conflator = Conflator(app_name="polytope", model=DatacubeConfig, argparser=parser)
        datacube_config = conflator.load()
        print(datacube_config)

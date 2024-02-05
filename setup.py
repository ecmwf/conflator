import io
import re

from setuptools import find_packages, setup

__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open("conflator/version.py", encoding="utf_8_sig").read(),
).group(1)


setup(
    name="conflator",
    version=__version__,
    description="""Load small app configurations from environment variables, command line arguments and config files,
                according to a pydantic model.""",
    long_description="",
    url="https://github.com/ecmwf/conflator",
    author="ECMWF",
    author_email="James.Hawkes@ecmwf.int",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
)

from setuptools import find_packages
from setuptools import setup

__version__ = "0.1"

setup(
    name="bff_api",
    version=__version__,
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "flask",
        "marshmallow",
        "boto3",
        "flask_cors"
    ]
)

# to run:
# create new env
# conda create --name bfftestenv
# list env: conda env list
# activate the env
# install pip
# conda install pip
# pip install .
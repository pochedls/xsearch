from setuptools import find_packages, setup

version = '0.0.5'

packages = find_packages(include=['xsearch'])

setup(
    name="xsearch",
    version=version,
    author="@pochedls",
    description="xsearch search utility",
    url="https://github.com/pochedls/xsearch",
    packages=packages,
)


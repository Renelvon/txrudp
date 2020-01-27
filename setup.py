"""Setup module for txrudp."""

import codecs
from os import path
import sys

from setuptools import setup


_HERE = path.abspath(path.dirname(__file__))
with codecs.open(path.join(_HERE, "README.rst"), encoding="utf-8") as f:
    _LONG_DESCRIPTION = f.read()

setup(
    version="0.5.2",
    long_description=_LONG_DESCRIPTION,
    packages=("txrudp", "tests"),
    extras_require={"crypto": ("pynacl",)},
    test_suite="nose.collector",
    include_package_data=True,
)

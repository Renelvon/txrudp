"""Setup module for txrudp."""

import codecs
from os import path
import sys

from setuptools import setup


_HERE = path.abspath(path.dirname(__file__))
with codecs.open(path.join(_HERE, 'README.rst'), encoding='utf-8') as f:
    _LONG_DESCRIPTION = f.read()

setup(
    name='txrudp',
    version='0.3.0',
    description='A Twisted extension implementing RUDP',
    long_description=_LONG_DESCRIPTION,
    url='https://github.com/Renelvon/txrudp',
    author='Nikolaos Korasidis',
    author_email='renelvon@gmail.com',
    license='MIT',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: System :: Networking'
    ),
    keywords='rudp twisted reliable',
    packages=('txrudp', 'tests'),
    install_requires=('enum34', 'protobuf', 'twisted'),
    tests_require=('coverage', 'nose', 'mock'),
    test_suite='tests',
    zip_safe=False
)

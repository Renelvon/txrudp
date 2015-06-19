"""Setup module for txrudp."""

import codecs
from os import path
import sys

from setuptools import find_packages, setup


_HERE = path.abspath(path.dirname(__file__))
with codecs.open(path.join(_HERE, 'README.md'), encoding='utf-8') as f:
    _LONG_DESCRIPTION = f.read()

requirements = ('jsonschema', 'twisted')
python_version = sys.version_info
if python_version.major < 3 or python_version.minor < 4:
    requirements.append('enum34')

setup(
    name='txrudp',
    version='0.1.0',
    description='A Twisted extension implementing RUDP',
    long_description=_LONG_DESCRIPTION,
    url='https://github.com/Renelvon/txrudp',
    author='Nikolaos Korasidis',
    author_email='renelvon@gmail.com',
    license='MIT',
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Networking'
    ),
    keywords='rudp twisted reliable',
    packages=find_packages(exclude=('tests',)),
    install_requires=requirements,
    extras_require={
        'dev': ('coverage', 'mock', 'nose', 'prospector')
    },
    zip_safe=False
)

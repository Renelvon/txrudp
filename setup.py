from codecs import open
from os import path

from setuptools import find_packages, setup


if __name__ == '__main__':
    here = path.abspath(path.dirname(__file__))
    with open(path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()

    setup(
        name='txrudp',
        version='0.1.0',
        description='A Twisted extension implementing RUDP',
        long_description=long_description,
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
        keywords=('rudp', 'twisted', 'reliable'),
        packages=find_packages(exclude=('tests',)),
        install_requires=('twisted',),
    )

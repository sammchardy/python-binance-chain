#!/usr/bin/env python
import codecs
import os
import re
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def install_requires():

    requires = [
        'pywallet>=0.1.0', 'requests>=2.21.0', 'websockets>=7.0', 'aiohttp>=3.5.4',
        'secp256k1>=0.13.2', 'protobuf>=3.6.1', 'mnemonic>=0.18'
    ]
    return requires


setup(
    name='python-binance-chain',
    version=find_version("binance_chain", "__init__.py"),
    packages=find_packages(),
    description='Binance Chain HTTP API python implementation',
    url='https://github.com/sammchardy/python-binance-chain',
    author='Sam McHardy',
    license='MIT',
    author_email='',
    install_requires=install_requires(),
    extras_require={
        'ledger': ['btchip-python>=0.1.28', ],
    },
    keywords='binance dex exchange rest api bitcoin ethereum btc eth bnb ledger',
    classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

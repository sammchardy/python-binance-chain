#!/usr/bin/env python
import codecs
import os
import re
from setuptools import setup

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
        'requests', 'websockets', 'jsonrpcclient[requests,websockets]', 'secp256k1', 'protobuf', 'mnemonic', 'pywallet'
    ]
    return requires


setup(
    name='python-binance-chain',
    version=find_version("binance_chain", "__init__.py"),
    packages=['binance_chain'],
    description='Binance Chain HTTP API python implementation',
    url='https://github.com/sammchardy/python-binance-chain',
    author='Sam McHardy',
    license='MIT',
    author_email='',
    install_requires=install_requires(),
    keywords='binance dex exchange rest api bitcoin ethereum btc eth bnb',
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

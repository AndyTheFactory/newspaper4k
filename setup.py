#!/bin/python
# -*- coding: utf-8 -*-
"""
Andrei Paraschiv-- https://github.com/AndyTheFactory
"""

import sys
import os
import codecs


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


packages = [
    "newspaper",
]


if sys.argv[-1] == "publish":
    os.system("python3 setup.py sdist upload -r pypi")
    sys.exit()

if sys.version_info < (3, 8):
    sys.exit("Sorry, Python < 3.8 is not supported")


with open("requirements.txt", encoding="utf-8") as f:
    required_packages = f.read().splitlines()


with codecs.open("README.rst", "r", "utf-8") as f:
    readme = f.read()


setup(
    name="newspaper4k",
    version="0.9.0",
    description="Simplified python article discovery & extraction.",
    long_description=readme,
    author="Andrei Paraschiv",
    author_email="andrei@thephpfactory.com",
    url="https://github.com/AndyTheFactory/newspaper4k",
    packages=packages,
    python_requires=">=3.8",
    include_package_data=True,
    install_requires=required_packages,
    license="MIT",
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
        "Topic :: Text Processing",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
    ],
)

#!/usr/bin/env python
#! -*- encoding: utf-8 -*-

__author__ = "joaonrb"

try:
    import testfm
except ImportError:
    raise LookupError("You must have test.fm >= 1.0.4 installed before (https://github.com/grafos-ml/frappe)")

import os
from setuptools import setup
from setuptools import find_packages


def get_requirements():
    with open("requirements.dev.txt") as reqs_file:
        reqs = [x.replace("\n", "").strip() for x in reqs_file if bool(x.strip()) and not x.startswith("#") and
                not x.startswith("https://")]
        return reqs


with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="frappe",
    version="1.2.0",
    description="Frappe recommendation system backend.",
    author="Linas Baltrunas",
    author_email="linas@tid.com",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={
        "": ["*.txt"],
    },
    license="copyright.txt",
    include_package_data=True,
    install_requires=get_requirements(),
    long_description=README,
)
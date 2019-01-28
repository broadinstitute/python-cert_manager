#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cert-manager-api",
    version="0.1.0",
    author="Andrew Teixeira",
    author_email="teixeira@broadinstitute.org",
    description="Python interface to the Sectigo Certificate Manager REST API",
    keywords=["sectigo", "comodo", "certificate"],
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/broadinstitute/cert_manager_api",
    packages=setuptools.find_packages(exclude=("tests")),
    use_scm_version=True,
    setup_requires=["setuptools_scm", "twine"],
    extras_require={
        "test": ["unittest2", "green"],
    },
    python_requires=">=2.7, <4",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

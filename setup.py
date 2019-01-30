#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Install cert_manager."""

import io
import setuptools

from cert_manager import APP_VERSION


def get_long_description():
    """Retrieve the long description from the README file."""
    # Use io.open to support encoding on Python 2 and 3
    fileh = io.open("README.md", "r", encoding="utf8")
    # ld = markdown2.markdown(fh.read())
    desc = fileh.read()
    fileh.close()

    return desc


setuptools.setup(
    name="cert_manager",
    version=APP_VERSION,
    author="Andrew Teixeira",
    author_email="teixeira@broadinstitute.org",
    description="Python interface to the Sectigo Certificate Manager REST API",
    include_package_data=True,
    keywords=["sectigo", "comodo", "certificate"],
    license="BSD",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=("tests")),
    url="https://github.com/broadinstitute/python-cert_manager",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    install_requires=["requests <3"],
    python_requires=">=2.7, <4",
    setup_requires=["setuptools_scm"],
)

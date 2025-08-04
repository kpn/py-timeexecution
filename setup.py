#!/usr/bin/env python
# setuptools doesn't support type hints for now:
# https://github.com/pypa/setuptools/issues/2345
# so we ignoring mypy checks on this package
from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()


setup(
    name="timeexecution",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Python project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="KPN DE Platform",
    author_email="de-platform@kpn.com",
    url="https://github.com/kpn/py-timeexecution",
    install_requires=[
        "pkgsettings>=0.9.2",
        "fqn-decorators>=1.2.5,<3.0.0",
        "typing-extensions>=4.5.0,<5.0.0",
    ],
    extras_require={
        "all": ["elasticsearch>=8.0.0,<10.0.0"],
        "elasticsearch": ["elasticsearch>=8.0.0,<10.0.0"],
    },
    packages=find_packages(exclude=["tests*"]),
    tests_require=["tox"],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

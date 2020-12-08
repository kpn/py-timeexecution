#!/usr/bin/env python
# setuptools doesn't support type hints for now:
# https://github.com/pypa/setuptools/issues/2345
# so we ignoring mypy checks on this package
from setuptools import find_packages, setup

with open("README.rst") as f:
    long_description = f.read()


setup(
    name="timeexecution",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Python project",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="KPN DE Platform",
    author_email="de-platform@kpn.com",
    url="https://github.com/kpn-digital/py-timeexecution",
    install_requires=[
        "pkgsettings>=0.9.2",
        "fqn-decorators>=1.2.5,<3.0.0",
    ],
    extras_require={
        "all": ["elasticsearch>=5.0.0,<7.0.0"],
        "elasticsearch": ["elasticsearch>=5.0.0,<7.0.0"],
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

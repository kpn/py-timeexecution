#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pkgversion import list_requirements, pep440_version, write_setup_py
from setuptools import find_packages

extra_dependencies = {
    "elasticsearch": list_requirements('requirements/requirements-elasticsearch.txt'),
    "influxdb": list_requirements('requirements/requirements-influxdb.txt'),
    "kafka": list_requirements('requirements/requirements-kafka.txt'),
}

extra_dependencies["all"] = list(set(sum(extra_dependencies.values(), [])))

write_setup_py(
    name='timeexecution',
    version=pep440_version(),
    description="Python project",
    long_description=open('README.rst').read(),
    author="KPN DE Platform",
    author_email='de-platform@kpn.com',
    url='https://github.com/kpn-digital/py-timeexecution',
    install_requires=list_requirements('requirements/requirements-base.txt'),
    extras_require=extra_dependencies,
    packages=find_packages(exclude=['tests*']),
    tests_require=['tox'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)

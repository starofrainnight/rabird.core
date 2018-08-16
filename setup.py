#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
import os.path
import sys
import shutil
import logging
import fnmatch

from setuptools import setup, find_packages
from pkg_resources import parse_version

with open('README.rst', encoding='utf-8') as readme_file, \
        open('HISTORY.rst', encoding='utf-8') as history_file:
    long_description = (readme_file.read() + "\n\n" + history_file.read())

install_requires = [
    'click>=6.0',
    'six>=1.3.0',
]

setup_requires = [
    'pytest-runner',
    # TODO(starofrainnight): put setup requirements (distutils extensions, etc.) here
]

tests_requires = [
    'pytest',
    # TODO: put package test requirements here
]

if sys.platform == "win32":
    # Require pywin32 package, but we use the pypiwin32 for install.
    try:
        import win32con
    except ImportError:
        current_version = parse_version(
            "%s.%s" % (sys.version_info.major, sys.version_info.minor))
        if current_version < parse_version('3.6'):
            # pypiwin32 not support versions below 3.6!
            install_requires.append("pypiwin32==219")
        else:
            # Latest pypiwin32 support python 3.6 and above
            install_requires.append("pypiwin32")
else:
    install_requires.append("linux_metrics")

if sys.version_info[0] == 2:
    install_requires.append("enum34")

setup(
    name='rabird.core',
    version='0.4.1',
    description="A library contained miscellaneous functions and fixes that used during our development",
    long_description=long_description,
    author="Hong-She Liang",
    author_email='starofrainnight@gmail.com',
    url='https://github.com/starofrainnight/rabird.core',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    license="Apache Software License",
    zip_safe=False,
    keywords='rabird.core',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=tests_requires,
    setup_requires=setup_requires,
)

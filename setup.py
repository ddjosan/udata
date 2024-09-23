#!/usr/bin/env python

import os

from setuptools import find_packages, setup


def file_content(filename):
    """Load file content"""
    with open(filename) as ifile:
        return ifile.read()


def pip(filename):
    """Return path to pip requirements file"""
    return file_content(os.path.join("requirements", filename))


long_description = "\n".join((file_content("README.md"), file_content("CHANGELOG.md"), ""))


install_requires = pip("install.pip")

setup(
    name="udata",
    version=__import__("udata").__version__,
    description=__import__("udata").__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://data.gov.rs',
    author='UNDP',
    author_email='pypi@data.gov.rs',
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "udata = udata.commands:cli",
        ],
       'udata.harvesters': [
            'statistika = udata.harvest.backends.statistika:StatistikaBackend',
            'statistika2021 = udata.harvest.backends.statistika2021:Statistika2021Backend',
            'sdg = udata.harvest.backends.sdg:SDGBackend',
            'rgz = udata.harvest.backends.rgz:RGZBackend',
        ],
        "udata.avatars": [
            "internal = udata.features.identicon.backends:internal",
            "adorable = udata.features.identicon.backends:adorable",
            "robohash = udata.features.identicon.backends:robohash",
        ],
        "pytest11": [
            "udata = udata.tests.plugin",
        ],
    },
    zip_safe=False,
    keywords='govrs opendata portal',
    license="GNU AGPLv3+",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: System :: Software Distribution",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ("License :: OSI Approved :: GNU Affero General Public License v3" " or later (AGPLv3+)"),
    ],
)

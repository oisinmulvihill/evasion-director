"""
Project's setuptool configuration.

This should eggify and in theory upload to pypi without problems.

Oisin Mulvihill
2008-12-23

"""
from setuptools import setup, find_packages

Name='evasion-director'
ProjecUrl="" #""
Version='1.0.0'
Author='Oisin Mulvihill'
AuthorEmail='oisinmulvihill at gmail dot com'
Maintainer=' Oisin Mulvihill'
Summary='This provides a daemon like running and monitoring application'
License=''
ShortDescription=Summary

# Recover the ReStructuredText docs:
fd = file("lib/director/docs/director.rtx")
Description=fd.read()
fd.close()

TestSuite = 'director.tests'

needed = [
    'configobj',
    'mako', 
    'evasion-messenger',
]

import sys
if not sys.platform.startswith('win'):
    needed.append('twisted')


#  find lib/director/viewpoint -type d -exec touch {}//__init__.py \;
#
# If new directories are added then I'll need to rerun this command.
#
EagerResources = [
]

ProjectScripts = [
    'scripts/director',
    'scripts/morbidsvr',
]

PackageData = {
    # If any package contains *.txt or *.rst files, include them:
    '': ['*.*'],
}

# Make exe versions of the scripts:
EntryPoints = {
}

setup(
#    url=ProjecUrl,
    zip_safe=False,
    name=Name,
    version=Version,
    author=Author,
    author_email=AuthorEmail,
    description=ShortDescription,
    long_description=Description,
    license=License,
    test_suite=TestSuite,
    scripts=ProjectScripts,
    install_requires=needed,
    packages=find_packages('lib'),
    package_data=PackageData,
    package_dir = {'': 'lib'},
    eager_resources = EagerResources,
    entry_points = EntryPoints,
)

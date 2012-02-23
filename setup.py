#!/usr/bin/env python
"""
Installation script:

To release a new version to PyPi:
- Ensure the version is correctly set in django-openkm.__init__.py
- Run: python setup.py sdist upload
"""

from setuptools import setup, find_packages

# Use 'final' as the 4th element to indicate
# a full release

VERSION = (0, 4, 0, 'alpha', 0)

def get_short_version():
    return '%s.%s' % (VERSION[0], VERSION[1])

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        # Append 3rd digit if > 0
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    elif VERSION[3] != 'final':
        version = '%s %s %s' % (version, VERSION[3], VERSION[4])
    return version

setup(name='django_openkm',
      version=get_version().replace(' ', '-'),
      url='https://github.com/tangentlabs/django-openkm',
      author="Phil Tysoe",
      author_email="philip.tysoe@tangentlabs.co.uk",
      description="A Python client library and functionality for the OpenKM document management system.",
      long_description="A Python client library for OpenKM document management system. Integrates with Django models, delegating document storage and retrieval to OpenKM",
      keywords="OpenKM, Django, document management",
      license='BSD',
      platforms=['linux'],
      packages=find_packages(exclude=["*.tests"]),
      install_requires=[
          'suds>=0.4',
          ],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: Unix',
                   'Programming Language :: Python']
      )


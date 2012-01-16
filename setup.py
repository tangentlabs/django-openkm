#!/usr/bin/env python
"""
Installation script:

To release a new version to PyPi:
- Ensure the version is correctly set in django-openkm.__init__.py
- Run: python setup.py sdist upload
"""

from setuptools import setup, find_packages

from django_openkm import get_version


setup(name='django_openkm',
      version=get_version().replace(' ', '-'),
      url='https://github.com/igniteflow/django-openkm',
      author="Phil Tysoe",
      author_email="philip.tysoe@tangentlabs.co.uk",
      description="A client library for OpenKM document management system.  Integration with Django 1.2+",
      long_description=open('README.rst').read(),
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


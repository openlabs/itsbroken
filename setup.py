#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
    It's broken setup

    :copyright: (c) 2010-2013 by Openlabs Technologies & Consulting (P) LTD
    :license: AGPLv3, see LICENSE for more details

'''
import os
import unittest
from setuptools import setup, Command


class TravisTest(Command):
    """
    Run the tests on Travis CI.

    Travis CI offers database settings which are different
    """
    description = "Run tests on Travis CI"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from openerp.tools import config
        config.options['db_user'] = 'postgres'
        config.options['db_host'] = 'localhost'
        config.options['db_port'] = 5432
        from tests import suite
        unittest.TextTestRunner(verbosity=3).run(suite())


execfile(os.path.join('itsbroken', 'version.py'))

setup(
    name='itsbroken',
    version=VERSION,        # noqa
    url='https://github.com/openlabs/itsbroken/',
    license='GNU Affero General Public License v3',
    author='Openlabs Technologies & Consulting (P) Limited',
    author_email='info@openlabs.co.in',
    description='OpenERP Unittesting Toolkit',
    long_description=open('README.rst').read(),
    packages=['itsbroken'],
    zip_safe=False,
    platforms='any',
    install_requires=[
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    test_suite='tests',
    cmdclass={
        'test_on_travis': TravisTest,
    }
)

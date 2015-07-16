# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages

name = 'onegov.core'
description = (
    'Contains code shared by all OneGov applications.'
)
version = '0.4.13'

dependencies = {
    'alembic',
    'arrow',
    'bleach',
    'cached_property',
    'chameleon',
    'click',
    'dogpile.cache',
    'fs',
    'itsdangerous',
    'isodate',
    'mailthon',
    'morepath>=0.11.1',
    'more.transaction',
    'more.webassets',
    'networkx',
    'onegov.server>=0.0.3',
    'passlib',
    'polib',
    'py-bcrypt',
    'python-magic',
    'psycopg2',
    'pylibmc',
    'pylru',
    'pyreact',
    'pytz',
    'purl',
    'sedate',
    'sqlalchemy>=0.9',
    'sqlparse',
    'translationstring',
    'unidecode',
    'webtest',
    'wtforms',
    'zope.sqlalchemy'
}


def get_long_description():
    readme = open('README.rst').read()
    history = open('HISTORY.rst').read()

    # cut the part before the description to avoid repetition on pypi
    readme = readme[readme.index(description) + len(description):]

    return '\n'.join((readme, history))

if os.environ.get('READTHEDOCS', None) == 'True':
    # on readthedocs.org we can't install c modules which is why we have
    # to mock them and exclude them from the setup
    # see also: http://docs.readthedocs.org/en/latest/faq.html

    dependencies -= {'pylibmc'}

setup(
    name=name,
    version=version,
    description=description,
    long_description=get_long_description(),
    url='http://github.com/seantis/onegov.core',
    author='Seantis GmbH',
    author_email='info@seantis.ch',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=name.split('.')[:-1],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=list(dependencies),
    extras_require=dict(
        test=[
            'coverage',
            'freezegun',
            'mock',
            'onegov.testing',
            'pytest-localserver'
        ],
    ),
    entry_points="""
        [console_scripts]
        onegov-core=onegov.core.cli:cli

        [onegov]
        upgrade=onegov.core.upgrade
    """,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ]
)

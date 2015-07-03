# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

name = 'onegov.town'
description = (
    'OneGov web application for small towns.'
)
version = '0.2.2'


def get_long_description():
    readme = open('README.rst').read()
    history = open('HISTORY.rst').read()

    # cut the part before the description to avoid repetition on pypi
    readme = readme[readme.index(description) + len(description):]

    return '\n'.join((readme, history))


setup(
    name=name,
    version=version,
    description=description,
    long_description=get_long_description(),
    url='http://github.com/onegov/onegov.town',
    author='Seantis GmbH',
    author_email='info@seantis.ch',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=name.split('.')[:-1],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'click',
        'cssmin',
        'jsmin',
        'lazy-object-proxy',
        'lxml',
        'onegov.core>=0.4.5',
        'onegov.form>=0.6.3',
        'onegov.foundation',
        'onegov.people>=0.0.1',
        'onegov.page>=0.1.0',
        'onegov.user',
        'pillow',
        'purl',
        'python-magic',
        'pytz',
        'translationstring',
    ],
    extras_require=dict(
        test=[
            'coverage',
            'onegov.testing',
            'mock',
            'webtest',
            'pyquery'
        ],
    ),
    entry_points="""
        [console_scripts]
        onegov-town=onegov.town.cli:cli

        [onegov]
        upgrade=onegov.town.upgrade
    """,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ]
)

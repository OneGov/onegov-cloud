# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

name = 'onegov.form'
description = (
    'Common OneGov form library based on WTForms.'
)
version = '0.5.2'


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
    url='http://github.com/seantis/onegov.form',
    author='Seantis GmbH',
    author_email='info@seantis.ch',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=name.split('.')[:-1],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'delorean',
        'humanize',
        'jsonpickle',
        'onegov.core>=0.3.5',
        'pyparsing',
        'pyyaml',
        'python-magic',
        'python-stdnum',
        'sqlalchemy_utils',
        'wtforms',
        'wtforms-components[color]',
        'unidecode'
    ],
    extras_require=dict(
        test=[
            'coverage',
            'onegov.testing',
            'pytest',
            'webob',
            'werkzeug'
        ],
    ),
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ]
)

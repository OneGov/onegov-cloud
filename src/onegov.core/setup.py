from setuptools import setup, find_packages

name = 'onegov.core'
description = (
    'Contains code shared by all OneGov applications.'
)
version = '0.30.1'


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
    url='http://github.com/onegov/onegov.core',
    author='Seantis GmbH',
    author_email='info@seantis.ch',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=name.split('.')[:-1],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'alembic',
        'arrow',
        'babel',
        'blinker',
        'bcrypt',
        'bleach',
        'cached_property',
        'chameleon',
        'click',
        'dill',
        'dogpile.cache',
        'editdistance',
        'fs',
        'html2text',
        'itsdangerous',
        'isodate',
        'lazy-object-proxy',
        'mailthon>=0.1.1',
        'morepath>=0.16',
        'more.transaction>=0.5',
        'more.webassets>=0.3.1',
        'networkx',
        'onegov.server>=0.3.2',
        'ordered-set',
        'passlib',
        'polib',
        'python-magic>=0.4.12',
        'python-memcached>=1.57',
        'psycopg2',
        'pylru',
        'pycurl',
        'pyreact',
        'pytz',
        'purl',
        'sedate',
        'sqlalchemy>=0.9',
        'sqlalchemy-utils',
        'sqlparse',
        'translationstring',
        'unidecode',
        'webtest',
        'wtforms',
        'xlrd',
        'xlsxwriter',
        'zope.sqlalchemy'
    ],
    extras_require=dict(
        test=[
            'coverage',
            'freezegun',
            'onegov.testing',
            'openpyxl',
            'pytest-localserver',
            'requests'
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
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ]
)

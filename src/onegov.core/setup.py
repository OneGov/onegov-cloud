from setuptools import setup, find_packages

name = 'onegov.core'
description = (
    'Contains code shared by all OneGov applications.'
)
version = '0.78.3'


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
    python_requires='>=3.6',
    install_requires=[
        'alembic',
        'arrow',
        'babel>=2.6.0',
        'blinker',
        'bcrypt',
        'bleach>=3.0.0',
        'cached_property',
        'chameleon>=3.0.0',
        'click',
        'dill!=0.2.7',
        'dogpile.cache',
        'editdistance',
        'fastcache',
        'fs>=2.0.0',
        'hiredis',
        'html2text',
        'itsdangerous',
        'isodate',
        'lazy-object-proxy',
        'mistletoe',
        'mailthon>=0.1.1',
        'morepath>=0.18',
        'more.content_security',
        'more.transaction>=0.5',
        'more.webassets>=0.3.1',
        'onegov.server>=0.7.0',
        'ordered-set',
        'passlib',
        'polib',
        'psqlparse',
        'python-magic>=0.4.12',
        'psycopg2',
        'pycurl',
        'pyreact',
        'pytz',
        'purl',
        'redis!=3.1.0',
        'rcssmin',
        'sedate',
        'sqlalchemy>=1.2.4',
        'sqlalchemy-utils',
        'sqlparse',
        'translationstring',
        'toposort',
        'unidecode',
        'webtest',
        'wtforms',
        'xlrd',
        'xlsxwriter',
        'yubico-client',
        'zope.sqlalchemy'
    ],
    extras_require=dict(
        test=[
            'coverage',
            'freezegun',
            'onegov_testing',
            'openpyxl',
            'pyquery',
            'pytest-localserver',
            'pytest-rerunfailures',
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

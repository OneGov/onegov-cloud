from setuptools import setup, find_packages

name = 'onegov.agency'
description = (
    'Administrative units and relationships for administrative directories.'
)
version = '1.12.0'


def get_long_description():
    readme = open('README.rst').read()
    history = open('HISTORY.rst').read()
    return '\n'.join((readme, history))


setup(
    name=name,
    version=version,
    description=description,
    long_description=get_long_description(),
    url='http://github.com/onegov/onegov.agency',
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
        'cached_property',
        'bleach',
        'html5lib',
        'onegov.core',
        'onegov.form',
        'onegov.file',
        'onegov.org>=1.1.10',
        'onegov.people>=0.10.0',
        'onegov.pdf>=0.4.0',
        'pyyaml',
        'xlrd',
    ],
    extras_require=dict(
        test=[
            'coverage',
            'freezegun',
            'mock',
            'onegov_testing',
            'pyquery',
            'PyPDF2',
            'pytest-localserver',
            'pytest>=3.0.0',
            'webtest',
        ],
    ),
    entry_points={
        'morepath': [
            'scan = onegov.agency'
        ],
        'onegov': [
            'upgrade = onegov.agency.upgrade'
        ],
        'console_scripts': [
            'onegov-agency=onegov.agency.cli:cli'
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ]
)

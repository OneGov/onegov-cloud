from setuptools import setup, find_packages

name = 'onegov.gazette'
description = (
    'OneGov official notices website.'
)
version = '0.0.4'


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
    url='http://github.com/onegov/onegov.gazette',
    author='Seantis GmbH',
    author_email='info@seantis.ch',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=name.split('.')[:-1],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'babel',
        'cached_property',
        'cssmin',
        'onegov.chat',
        'onegov.core',
        'onegov.form',
        'onegov.foundation',
        'onegov.notice',
        'onegov.shared',
        'onegov.user',
        'pyyaml',
        'raven',
        'rjsmin'
    ],
    extras_require=dict(
        test=[
            'coverage',
            'freezegun',
            'mock',
            'onegov_testing',
            'pyquery',
            'pytest-localserver',
            'pytest',
            'webtest',
        ],
    ),
    entry_points={
        'morepath': [
            'scan = onegov.gazette'
        ],
        'onegov': [
            'upgrade = onegov.gazette.upgrade'
        ],
        'console_scripts': [
            'onegov-gazette=onegov.gazette.cli:cli'
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ]
)

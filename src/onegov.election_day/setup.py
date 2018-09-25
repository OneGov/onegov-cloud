from setuptools import setup, find_packages

name = 'onegov.election_day'
description = (
    'OneGov ballot results website used on election day.'
)
version = '3.6.9'


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
    url='http://github.com/onegov/onegov.election_day',
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
        'arrow>=0.8.0',
        'babel>=2.6.0',
        'cached_property',
        'cssmin',
        'onegov.core>=0.64',
        'onegov.ballot>=3.7.1',
        'onegov.form>=0.37.0',
        'onegov.foundation>=0.0.4',
        'onegov.pdf>=0.2.0',
        'onegov.shared>=0.2.0',
        'onegov.user>=0.17.1',
        'pyyaml',
        'raven',
        'requests',
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
            'pytest>=3.0.0',
            'webtest',
        ],
    ),
    entry_points={
        'morepath': [
            'scan = onegov.election_day'
        ],
        'onegov': [
            'upgrade = onegov.election_day.upgrade'
        ],
        'console_scripts': [
            'onegov-election-day=onegov.election_day.cli:cli'
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

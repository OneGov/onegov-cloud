from setuptools import setup, find_packages

name = 'onegov.wtfs'
description = 'Tax form scanning app for the city of Winterthur'
version = '0.0.7'


def get_long_description():
    readme = open('README.rst').read()
    history = open('HISTORY.rst').read()
    readme = readme[readme.index(description) + len(description):]
    return '\n'.join((readme, history))


setup(
    name=name,
    version=version,
    description=description,
    long_description=get_long_description(),
    url='http://github.com/onegov/onegov.wtfs',
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
        'onegov.chat',
        'onegov.core',
        'onegov.file',
        'onegov.form',
        'onegov.foundation',
        'onegov.shared',
        'onegov.user',
        'python-dateutil',
        'raven',
        'requests',
        'rjsmin',
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
            'scan = onegov.wtfs'
        ],
        'onegov': [
            'upgrade = onegov.wtfs.upgrade'
        ],
        'console_scripts': [
            'onegov-wtfs=onegov.wtfs.cli:cli'
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

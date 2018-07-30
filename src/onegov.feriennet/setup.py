from setuptools import setup, find_packages

name = 'onegov.feriennet'
description = (
    'Ferienpass Management for Pro Juventute'
)
version = '1.3.34'


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
    url='http://github.com/OneGov/onegov.feriennet',
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
        'faker',
        'icalendar',
        'onegov.activity',
        'onegov.core>=0.70.5',
        'onegov.org>=0.20.0',
    ],
    extras_require=dict(
        test=[
            'coverage',
            'freezegun',
            'onegov_testing',
            'pytest',
            'pytest-localserver',
            'pyquery',
            'requests-mock',
            'ulid'
        ],
    ),
    entry_points={
        'onegov': [
            'upgrade = onegov.feriennet.upgrade'
        ],
        'console_scripts': [
            'onegov-feriennet=onegov.feriennet.cli:cli'
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

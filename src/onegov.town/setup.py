from setuptools import setup, find_packages

name = 'onegov.town'
description = (
    'OneGov web application for small towns.'
)
version = '1.13.1'


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
        'onegov.org>=0.5.0',
    ],
    extras_require=dict(
        test=[
            'coverage',
            'morepath',
            'freezegun',
            'onegov.testing',
            'webtest',
            'pyquery',
            'pytest-localserver'
        ],
    ),
    entry_points="""
        [console_scripts]
        onegov-town=onegov.org.cli:cli

        [onegov]
        upgrade=onegov.town.upgrade
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

from setuptools import setup, find_packages

name = 'onegov_testing'
description = (
    'Contains testing code shared by all OneGov Cloud applications.'
)
version = '0.0.1'


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
    url='http://github.com/OneGov/onegov_testing',
    author='Seantis GmbH',
    author_email='info@seantis.ch',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=name.split('.')[:-1],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'coverage',
        'elasticsearch',
        'mirakuru',
        'onegov.core',
        'Pillow',
        'port-for',
        'pytest>=3.0.6',
        'fs==2.0.10a1',
        'sqlalchemy',
        'splinter',
        'webdriver-manager',
        'testing.postgresql',
    ],
    entry_points={
        'pytest11': [
            'onegov_testing = onegov_testing',
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ]
)

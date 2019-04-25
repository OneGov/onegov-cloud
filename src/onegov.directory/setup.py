from setuptools import setup, find_packages

name = 'onegov.directory'
description = (
    'Directories for the OneGov Cloud.'
)
version = '0.4.7'


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
    url='http://github.com/OneGov/onegov.directory',
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
        'more_itertools',
        'onegov.core>=0.4.0',
        'onegov.file',
        'onegov.form>=0.31.0',
        'onegov.gis',
        'onegov.search',
        'pyyaml',
    ],
    extras_require=dict(
        test=[
            'coverage',
            'onegov_testing',
            'pytest',
        ],
    ),
    entry_points={
        'onegov': [
            'upgrade = onegov.directory.upgrade'
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

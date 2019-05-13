from setuptools import setup, find_packages

name = 'onegov.swissvotes'
description = 'Database for federal votes'
version = '1.0.1'


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
    url='http://github.com/onegov/onegov.swissvotes',
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
        'onegov.core>=v0.79.1',
        'onegov.file>=0.10.0',
        'onegov.form>=0.40.0',
        'onegov.foundation',
        'onegov.quill>=0.4.0',
        'onegov.shared',
        'onegov.user',
        'python-dateutil',
        'requests',
        'rjsmin',
        'xlrd',
        'xlsxwriter',
    ],
    extras_require=dict(
        test=[
            'coverage',
            'freezegun',
            'mock',
            'onegov_testing',
            'onegov.pdf',
            'pyquery',
            'pytest-localserver',
            'pytest>=3.0.0',
            'webtest',
        ],
    ),
    entry_points={
        'morepath': [
            'scan = onegov.swissvotes'
        ],
        'onegov': [
            'upgrade = onegov.swissvotes.upgrade'
        ],
        'console_scripts': [
            'onegov-swissvotes=onegov.swissvotes.cli:cli'
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

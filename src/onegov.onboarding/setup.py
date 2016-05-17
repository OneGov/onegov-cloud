from setuptools import setup, find_packages

name = 'onegov.onboarding'
description = (
    'Onboarding for OneGov Cloud applications.'
)
version = '0.2.5'


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
    url='http://github.com/OneGov/onegov.onboarding',
    author='Seantis GmbH',
    author_email='info@seantis.ch',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=name.split('.')[:-1],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'cached_property',
        'onegov.core>=0.20.1',
        'onegov.foundation',
        'onegov.libres',
        'onegov.town>=1.8.0',
        'python-simple-hipchat',
    ],
    extras_require=dict(
        test=[
            'coverage',
            'onegov.testing',
            'pytest',
            'pytest-localserver',
            'pyquery',
            'webtest'
        ],
    ),
    entry_points={
        'onegov': [
            'upgrade = onegov.onboarding.upgrade'
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

from setuptools import setup, find_packages

name = 'onegov.org'
description = (
    'A OneGov Cloud base application for organisations.'
)
version = '1.2.5'


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
    url='http://github.com/OneGov/onegov.org',
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
        'babel',
        'click',
        'icalendar',
        'isodate',
        'lxml',
        'onegov.chat',
        'onegov.core>=0.41.0',
        'onegov.directory>=0.4.1',
        'onegov.event>=1.1.0',
        'onegov.file>=0.2.1',
        'onegov.form>=0.18.0',
        'onegov.foundation>=0.0.7',
        'onegov.gis',
        'onegov.newsletter>=0.1.0',
        'onegov.page>=0.1.0',
        'onegov.pay',
        'onegov.people>=0.9.1',
        'onegov.recipient',
        'onegov.reservation>=0.3.0',
        'onegov.search>=1.0.0',
        'onegov.shared',
        'onegov.ticket>=0.4.1',
        'onegov.user>=0.11.0',

        # Pillow 5.4.0 has a number of problems related to PNG
        'Pillow!=5.4.0',

        'purl',
        'python-dateutil',
        'python-magic>=0.4.12',
        'pytz',
        'PyYAML',
        'rjsmin',
        'sedate',
        'translationstring',
        'tqdm',
        'webtest',
    ],
    extras_require=dict(
        test=[
            'coverage',
            'freezegun',
            'onegov_testing',
            'pyquery',
            'pytest-localserver',
            'requests-mock',
            'vcrpy',
        ],
    ),
    entry_points={
        'onegov': [
            'upgrade = onegov.org.upgrade'
        ],
        'console_scripts': [
            'onegov-org=onegov.org.cli:cli'
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

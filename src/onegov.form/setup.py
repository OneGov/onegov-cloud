from setuptools import setup, find_packages

name = 'onegov.form'
description = (
    'Common OneGov form library based on WTForms.'
)
version = '0.39.2'


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
    url='http://github.com/onegov/onegov.form',
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
        'cached_property',
        'chameleon',
        'colour>=0.0.4',
        'humanize',
        'jsonpickle',
        'mistune',
        'more.webassets',
        'onegov.core>=0.70.5',
        'onegov.file',
        'onegov.pay',
        'onegov.search',
        'phonenumbers',
        'pyparsing!=2.1.2',  # 2.1.2 has a problem with Python 3
        'pyyaml',
        'python-dateutil',
        'python-stdnum',
        'sedate',
        'sqlalchemy_utils',
        'wtforms>=2.2',

        # be careful to add extras for wtforms-components by including the
        # needed packages, not by using square brackets, pip doesn't do well
        # with square brackets (the install on the server won't work)
        'wtforms-components',

        'unidecode'
    ],
    extras_require=dict(
        test=[
            'coverage',
            'onegov_testing',
            'pytest',
            'pytest-localserver',
            'webob',
            'werkzeug'
        ],
    ),
    entry_points={
        'onegov': [
            'upgrade = onegov.form.upgrade'
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

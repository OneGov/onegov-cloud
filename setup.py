
from setuptools import setup

setup(
    name='onegov-cloud',
    version='1.0.0',
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['onegov'],
    packages=[
        'onegov.activity',
        'onegov.agency',
        'onegov.async_http',
        'onegov.ballot',
        'onegov.chat',
        'onegov.core',
        'onegov.directory',
        'onegov.election_day',
        'onegov.event',
        'onegov.feriennet',
        'onegov.file',
        'onegov.form',
        'onegov.foundation',
        'onegov.foundation6',
        'onegov.fsi',
        'onegov.gazette',
        'onegov.gis',
        'onegov.intranet',
        'onegov.newsletter',
        'onegov.notice',
        'onegov.onboarding',
        'onegov.org',
        'onegov.page',
        'onegov.pay',
        'onegov.pdf',
        'onegov.people',
        'onegov.qrcode',
        'onegov.quill',
        'onegov.recipient',
        'onegov.reservation',
        'onegov.search',
        'onegov.server',
        'onegov.shared',
        'onegov.stepsequence',
        'onegov.swissvotes',
        'onegov.ticket',
        'onegov.town',
        'onegov.town6',
        'onegov.user',
        'onegov.winterthur',
        'onegov.wtfs',
        'onegov.translator_directory',
    ],
    install_requires=[
        'AIS2.py',
        'aiohttp',
        'Pillow',
        'PyYAML',
        'alembic',
        'arrow',
        'attrs',
        'babel',
        'bcrypt',
        'bjoern',
        'bleach',
        'blinker',
        'cached_property',
        'chameleon==3.7.4',
        'certifi',
        'click',
        'colour',
        'cssmin',
        'cssutils',
        'dill',
        'dogpile.cache',
        'dukpy',
        'editdistance',
        'elasticsearch>=7.0.0,<8.0.0',
        'elasticsearch-dsl>=7.0.0,<8.0.0',
        'faker',
        'fastcache',
        'filedepot',
        'fs',
        'furl',
        'genshi',
        'hiredis',
        'html2text',
        'html5lib',
        'humanize',
        'icalendar',
        'isodate',
        'itsdangerous',
        'jsonpickle',
        'kerberos',
        'langdetect',
        'lazy-object-proxy',
        'ldap3',
        'libres',
        'libsass',
        'lxml',
        'mistletoe',
        'mistune',
        'more.content_security',
        'more.transaction',
        'more.webassets',
        'more_itertools',
        'morepath',
        'msal',
        'ordered-set',
        'openpyxl',
        'passlib',
        'pdfdocument',
        'pdfrw',
        'pdftotext',
        'phonenumbers',
        'polib',
        'psqlparse',
        'psycopg2',
        'purl',
        'pycurl',
        'pyparsing',
        'pyquery',
        'qrbill',
        'qrcode',
        'pysaml2',
        'python-dateutil',
        'python-magic',
        'python-stdnum',
        'pytz',
        'pyyaml',
        'rcssmin',
        'redis',
        'reportlab',
        'requests',
        'rjsmin',
        'sedate',
        'sentry_sdk',
        'sortedcontainers',
        'sqlalchemy<1.4.0',
        'sqlalchemy-utils',
        'sqlparse',
        'stripe',
        'svglib',
        'toposort',
        'tqdm',
        'translationstring',
        'ua-parser',
        'ulid',
        'unidecode',
        'urlextract',
        'validate_email',
        'vobject',
        'watchdog',
        'webob',
        'webtest',
        'wtforms<=2.2.1',
        'wtforms-components',
        'xlrd',
        'xlsxwriter',
        'xtermcolor',
        'yubico-client',
        'zope.sqlalchemy',
    ],
    extras_require={
        'dev': [
            'pytest-profiling',
            'pytest-testmon',
            'pytest-xdist',
            'scrambler',
            'lingua==3.12',
            'gitpython==3.0.9',
            'honyaku@git+https://github.com/seantis/honyaku#egg=honyaku',
            'flake8'
        ],
        'docs': [
            'docutils',
            'alabaster',
            'Jinja2',
            'sphinx',
        ],
        'test': [
            'Pillow',
            'coverage',
            'findimports',
            'freezegun',
            'lxml',
            'mirakuru',
            'mock',
            'more.itsdangerous',
            'morepath',
            'port-for',
            'psutil',
            'pyquery',
            'pytest',
            'pytest-localserver<0.6',
            'pytest-redis',
            'pytest-rerunfailures',
            'pytest-timeout',
            'pyyaml',
            'requests',
            'requests-mock',
            'selenium',
            'splinter',
            'sqlalchemy',
            'testing.postgresql',
            'ulid',
            'vcrpy',
            'webdriver-manager',
            'webob',
            'webtest',
            'werkzeug',
        ],
    },
    entry_points={
        'morepath': [
            'scan=onegov'
        ],
        'console_scripts': [
            'onegov-agency=onegov.agency.cli:cli',
            'onegov-core=onegov.core.cli:cli',
            'onegov-election-day=onegov.election_day.cli:cli',
            'onegov-event=onegov.event.cli:cli',
            'onegov-feriennet=onegov.feriennet.cli:cli',
            'onegov-foundation=onegov.foundation6.cli:cli',
            'onegov-fsi=onegov.fsi.cli:cli',
            'onegov-gazette=onegov.gazette.cli:cli',
            'onegov-org=onegov.org.cli:cli',
            'onegov-pdf=onegov.pdf.cli:cli',
            'onegov-people=onegov.people.cli:cli',
            'onegov-search=onegov.search.cli:cli',
            'onegov-server=onegov.server.cli:run',
            'onegov-swissvotes=onegov.swissvotes.cli:cli',
            'onegov-town=onegov.org.cli:cli',
            'onegov-town6=onegov.org.cli:cli',
            'onegov-user=onegov.user.cli:cli',
            'onegov-winterthur=onegov.winterthur.cli:cli',
            'onegov-wtfs=onegov.wtfs.cli:cli',
            'onegov-translator=onegov.translator_directory.cli:cli',
        ],
        'onegov_upgrades': [
            'onegov.activity=onegov.activity.upgrade',
            'onegov.agency=onegov.agency.upgrade',
            'onegov.ballot=onegov.ballot.upgrade',
            'onegov.chat=onegov.chat.upgrade',
            'onegov.core=onegov.core.upgrade',
            'onegov.directory=onegov.directory.upgrade',
            'onegov.election_day=onegov.election_day.upgrade',
            'onegov.event=onegov.event.upgrade',
            'onegov.feriennet=onegov.feriennet.upgrade',
            'onegov.file=onegov.file.upgrade',
            'onegov.form=onegov.form.upgrade',
            'onegov.foundation=onegov.foundation.upgrade',
            'onegov.fsi=onegov.fsi.upgrade',
            'onegov.gazette=onegov.gazette.upgrade',
            'onegov.gis=onegov.gis.upgrade',
            'onegov.intranet=onegov.intranet.upgrade',
            'onegov.newsletter=onegov.newsletter.upgrade',
            'onegov.notice=onegov.notice.upgrade',
            'onegov.onboarding=onegov.onboarding.upgrade',
            'onegov.org=onegov.org.upgrade',
            'onegov.page=onegov.page.upgrade',
            'onegov.pay=onegov.pay.upgrade',
            'onegov.pdf=onegov.pdf.upgrade',
            'onegov.people=onegov.people.upgrade',
            'onegov.quill=onegov.quill.upgrade',
            'onegov.recipient=onegov.recipient.upgrade',
            'onegov.reservation=onegov.reservation.upgrade',
            'onegov.search=onegov.search.upgrade',
            'onegov.shared=onegov.shared.upgrade',
            'onegov.swissvotes=onegov.swissvotes.upgrade',
            'onegov.ticket=onegov.ticket.upgrade',
            'onegov.town=onegov.town.upgrade',
            'onegov.town6=onegov.town6.upgrade',
            'onegov.user=onegov.user.upgrade',
            'onegov.winterthur=onegov.winterthur.upgrade',
            'onegov.wtfs=onegov.wtfs.upgrade',
            'onegov.translator_directory=onegov.translator_directory.upgrade'
        ]
    })

# The current version set by do/release. Do not edit by hand!
#
# Note that during development this version information is stale. That is to
# say, we do not have a separate development version - the use for this
# version is to create release-dependent urls, artifacts and caches. During
# development these dependencies do not need to be updated in lock-step.
#
__version__ = '2019.19'

# The module levels used for dependency tests and to have a well defined
# onegov core upgrade order.
LEVELS = (
    # root
    (
        'onegov.server',
    ),

    # core
    (
        'onegov.core',
    ),

    # modules,
    (
        'onegov.activity',
        'onegov.ballot',
        'onegov.chat',
        'onegov.directory',
        'onegov.event',
        'onegov.file',
        'onegov.form',
        'onegov.foundation',
        'onegov.gis',
        'onegov.newsletter',
        'onegov.notice',
        'onegov.page',
        'onegov.pay',
        'onegov.pdf',
        'onegov.people',
        'onegov.quill',
        'onegov.recipient',
        'onegov.reservation',
        'onegov.search',
        'onegov.shared',
        'onegov.ticket',
        'onegov.user',
    ),

    # applications,
    (
        'onegov.agency',
        'onegov.election_day',
        'onegov.feriennet',
        'onegov.gazette',
        'onegov.intranet',
        'onegov.onboarding',
        'onegov.org',
        'onegov.swissvotes',
        'onegov.town',
        'onegov.winterthur',
        'onegov.wtfs',
    ),
)

import logging   # noqa
import warnings  # noqa

log = logging.getLogger('onegov.core')  # noqa
log.addHandler(logging.NullHandler())   # noqa

ignored_warnings = (
    # we will keep using psycopg2 instead of psycogp2-binary
    "The psycopg2 wheel package will be renamed from release 2.8",

    # SQLAlchemy-Utils installs its own array_agg function, which seems fine
    "The GenericFunction 'array_agg' is already registered"
)

for message in ignored_warnings:
    warnings.filterwarnings("ignore", message=message)

from onegov.core.framework import Framework # noqa
from onegov.core.filestorage import get_filestorage_file # noqa

# include the filters module so they get picked up by webassets
from onegov.core import filters  # noqa

__all__ = ['Framework', 'log']

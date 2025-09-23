# The current version set by do/release. Do not edit by hand!
#
# Note that during development this version information is stale. That is to
# say, we do not have a separate development version - the use for this
# version is to create release-dependent urls, artifacts and caches. During
# development these dependencies do not need to be updated in lock-step.
#
from __future__ import annotations

__version__ = '2025.51'

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
        'onegov.api',
        'onegov.async_http',
        'onegov.chat',
        'onegov.directory',
        'onegov.event',
        'onegov.file',
        'onegov.form',
        'onegov.foundation',
        'onegov.gis',
        'onegov.gever',
        'onegov.newsletter',
        'onegov.notice',
        'onegov.page',
        'onegov.parliament',
        'onegov.pay',
        'onegov.pdf',
        'onegov.people',
        'onegov.plausible',
        'onegov.quill',
        'onegov.qrcode',
        'onegov.recipient',
        'onegov.reservation',
        'onegov.search',
        'onegov.shared',
        'onegov.stepsequence',
        'onegov.ticket',
        'onegov.user',
        'onegov.websockets',
    ),

    # applications,
    (
        'onegov.agency',
        'onegov.election_day',
        'onegov.feriennet',
        'onegov.foundation6',
        'onegov.fsi',
        'onegov.gazette',
        'onegov.intranet',
        'onegov.landsgemeinde',
        'onegov.onboarding',
        'onegov.org',
        'onegov.pas',
        'onegov.swissvotes',
        'onegov.town6',
        'onegov.translator_directory',
        'onegov.winterthur',
    ),
)

import logging
import warnings

log = logging.getLogger('onegov.core')
log.addHandler(logging.NullHandler())

ignored_warnings = (
    # we will keep using psycopg2 instead of psycogp2-binary
    'The psycopg2 wheel package will be renamed from release 2.8',

    # SQLAlchemy-Utils installs its own array_agg function, which seems fine
    "The GenericFunction 'array_agg' is already registered"
)

for message in ignored_warnings:
    warnings.filterwarnings('ignore', message=message)

from onegov.core.framework import Framework
from onegov.core.filestorage import get_filestorage_file  # noqa: F401

# include the filters module so they get picked up by webassets
from onegov.core import filters  # noqa: F401

__all__ = ['Framework', 'log']

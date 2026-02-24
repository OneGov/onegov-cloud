from __future__ import annotations

import logging
log = logging.getLogger('onegov.election_day')
log.addHandler(logging.NullHandler())

from onegov.election_day.i18n import _

from onegov.election_day.app import ElectionDayApp

__all__ = ('_', 'log', 'ElectionDayApp')

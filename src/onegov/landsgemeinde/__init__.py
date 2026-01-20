from __future__ import annotations

import logging

log = logging.getLogger('onegov.landsgemeinde')
log.addHandler(logging.NullHandler())

from onegov.landsgemeinde.i18n import _

from onegov.landsgemeinde.app import LandsgemeindeApp

__all__ = (
    '_',
    'log',
    'LandsgemeindeApp'
)

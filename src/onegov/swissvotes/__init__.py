from __future__ import annotations

import logging
log = logging.getLogger('onegov.swissvotes')
log.addHandler(logging.NullHandler())

from onegov.swissvotes.i18n import _

from onegov.swissvotes.app import SwissvotesApp

__all__ = (
    '_',
    'log',
    'SwissvotesApp'
)

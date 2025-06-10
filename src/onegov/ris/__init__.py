from __future__ import annotations

import logging

log = logging.getLogger('onegov.ris')
log.addHandler(logging.NullHandler())

from onegov.ris.i18n import _

__all__ = (
    '_',
    'log'
)

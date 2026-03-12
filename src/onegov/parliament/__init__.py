from __future__ import annotations

import logging

log = logging.getLogger('onegov.parliament')
log.addHandler(logging.NullHandler())

from onegov.parliament.i18n import _

__all__ = (
    '_',
    'log'
)

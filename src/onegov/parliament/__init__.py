from __future__ import annotations

import logging

log = logging.getLogger('onegov.org')
log.addHandler(logging.NullHandler())

from onegov.org.i18n import _

__all__ = (
    '_',
    'log'
)

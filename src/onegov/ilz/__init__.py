from __future__ import annotations

import logging
log = logging.getLogger('onegov.ilz')
log.addHandler(logging.NullHandler())

from onegov.ilz.i18n import _

from onegov.ilz.app import ILZApp

__all__ = ('ILZApp', 'log', '_')

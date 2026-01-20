from __future__ import annotations

import logging
log = logging.getLogger('onegov.fsi')
log.addHandler(logging.NullHandler())

from onegov.fsi.i18n import _

from onegov.fsi.app import FsiApp

__all__ = ('FsiApp', 'log', '_')

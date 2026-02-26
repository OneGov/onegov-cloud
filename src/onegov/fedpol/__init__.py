from __future__ import annotations

import logging
log = logging.getLogger('onegov.fedpol')
log.addHandler(logging.NullHandler())

from onegov.fedpol.i18n import _

from onegov.fedpol.app import FedpolApp

__all__ = ('FedpolApp', 'log', '_')

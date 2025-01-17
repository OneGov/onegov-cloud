from __future__ import annotations

import logging
log = logging.getLogger('onegov.town')
log.addHandler(logging.NullHandler())

from onegov.town6.i18n import _

from onegov.town6.app import TownApp

__all__ = ['_', 'log', 'TownApp']

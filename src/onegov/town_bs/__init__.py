from __future__ import annotations

import logging
log = logging.getLogger('onegov.town_bs')
log.addHandler(logging.NullHandler())

from onegov.town6.i18n import _

from onegov.town_bs.app import TownBsApp

__all__ = ['_', 'log', 'TownBsApp']

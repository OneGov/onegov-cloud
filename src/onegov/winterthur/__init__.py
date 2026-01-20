from __future__ import annotations

import logging
log = logging.getLogger('onegov.winterthur')
log.addHandler(logging.NullHandler())

from onegov.winterthur.i18n import _

from onegov.winterthur.app import WinterthurApp

__all__ = ('WinterthurApp', 'log', '_')

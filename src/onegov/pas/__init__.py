from __future__ import annotations

import logging

log = logging.getLogger('onegov.pas')
log.addHandler(logging.NullHandler())

from onegov.pas.i18n import _
from onegov.pas.app import PasApp

# Import cronjobs to register the decorators
from onegov.pas import cronjobs

__all__ = (
    '_',
    'log',
    'PasApp',
    'cronjobs'
)

from __future__ import annotations

import logging
log = logging.getLogger('onegov.feriennet')
log.addHandler(logging.NullHandler())

from onegov.core.i18n.translation_string import TranslationStringFactory
_ = TranslationStringFactory('onegov.feriennet')

from onegov.feriennet.app import FeriennetApp

__all__ = ['_', 'log', 'FeriennetApp']

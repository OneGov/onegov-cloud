from __future__ import annotations

import logging
log = logging.getLogger('onegov.translator_directory')
log.addHandler(logging.NullHandler())

from onegov.translator_directory.i18n import _

from onegov.translator_directory.app import TranslatorDirectoryApp


__all__ = ('TranslatorDirectoryApp', 'log', '_')

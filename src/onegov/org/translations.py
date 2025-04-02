""" Contains a list of manual translations. Those are usually messages that
exist in external packages which provide no translations.

"""
from __future__ import annotations

from onegov.org import _

# messages defined in wtforms-components
_('Not a valid color.')
_('CSRF failed.')
_('CSRF token missing.')
_('CSRF token expired.')

# messages not translated by wtforms
_('Not a valid choice')

# Roles in plural form are not defined as translatable texts anywhere
_('Admins')
_('Editors')
_('Supporters')
_('Members')

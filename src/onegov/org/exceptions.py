from __future__ import annotations

from onegov.org.i18n import _
from webob.exc import HTTPLocked


class MTANAccessLimitExceeded(HTTPLocked):
    """
    Raised when a user exceeds the maximum number of unique accesses
    to protected resources.
    """
    title = _('mTAN Access Limit Exceeded')
    explanation = _(
        'You have exceeded the maximum number of unique accesses to '
        'protected resources. Please try again at a later date.'
    )

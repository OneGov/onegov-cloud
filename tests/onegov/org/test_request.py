from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from webob.exc import HTTPForbidden


def test_get_current_user_returns_user() -> None:
    user = MagicMock()
    request = MagicMock()
    request.current_user = user

    from onegov.org.request import OrgRequest
    result = OrgRequest.get_current_user(request)

    assert result is user


def test_get_current_user_raises_when_none() -> None:
    request = MagicMock()
    request.current_user = None
    request.is_logged_in = True
    request.current_username = 'stale@example.com'

    from onegov.org.request import OrgRequest
    with patch('onegov.org.request.sentry_sdk') as mock_sentry:
        with pytest.raises(HTTPForbidden):
            OrgRequest.get_current_user(request)

        mock_sentry.capture_message.assert_called_once_with(
            'current_user is None despite valid identity'
            ': stale@example.com',
            level='warning',
        )


def test_get_current_user_no_sentry_for_anonymous() -> None:
    request = MagicMock()
    request.current_user = None
    request.is_logged_in = False

    from onegov.org.request import OrgRequest
    with patch('onegov.org.request.sentry_sdk') as mock_sentry:
        with pytest.raises(HTTPForbidden):
            OrgRequest.get_current_user(request)

        mock_sentry.capture_message.assert_not_called()

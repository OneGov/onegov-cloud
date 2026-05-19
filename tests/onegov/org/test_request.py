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

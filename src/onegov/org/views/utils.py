from __future__ import annotations

from functools import lru_cache
from onegov.org.i18n import _
from onegov.user import Auth
from webob.exc import HTTPFound, HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


# FIXME: I think these would make more sense as cached_property on OrgRequest
@lru_cache(maxsize=1)
def show_tags(request: OrgRequest) -> bool:
    return request.app.org.event_filter_type in ('tags', 'tags_and_filters')


@lru_cache(maxsize=1)
def show_filters(request: OrgRequest) -> bool:
    return request.app.org.event_filter_type in ('filters', 'tags_and_filters')


def assert_citizen_logged_in(request: OrgRequest) -> None:
    if not request.app.org.citizen_login_enabled:
        raise HTTPNotFound()

    if not request.authenticated_email:
        request.info(
            _('Please enter your e-mail address in order to continue')
        )
        raise HTTPFound(location=request.link(
            Auth.from_request_path(request),
            name='citizen-login'
        ))

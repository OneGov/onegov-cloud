from __future__ import annotations

import os
import sys
import weakref

from onegov.core.framework import Framework
from onegov.core.orm import DB_CONNECTION_ERRORS
from morepath.core import excview_tween_factory  # type:ignore[import-untyped]
from sentry_sdk import capture_event, get_client
from sentry_sdk.integrations import Integration
from sentry_sdk.integrations._wsgi_common import RequestExtractor
from sentry_sdk.scope import Scope, should_send_default_pii
from sentry_sdk.tracing import SOURCE_FOR_STYLE
from sentry_sdk.utils import (
    capture_internal_exceptions,
    event_from_exception,
)
from webob.exc import HTTPException, HTTPServiceUnavailable


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed.wsgi import WSGIEnvironment
    from collections.abc import Callable
    from sentry_sdk._types import Event, EventProcessor, Hint
    from sentry_sdk.utils import ExcInfo
    from webob import Response
    from webob.cookies import RequestCookies
    from webob.request import _FieldStorageWithFile

    from .request import CoreRequest


# TODO: We may want to extract some of this into a MorepathIntegration
#       publish it as more.sentry and derive OneGovIntegration from that
#       we could even contribute it to sentry_sdk itself, although they
#       are usually less willing to take on additional maintenance tasks.
class OneGovCloudIntegration(Integration):
    """
    A Sentry SDK integration for OneGov Cloud, which relies on
    :class:`onegov.core.request.CoreRequest` to forward more
    detailed information to Sentry.
    """

    identifier = 'onegov-cloud'
    transaction_style = 'path'

    def __init__(self, with_wsgi_middleware: bool = True):
        self.with_wsgi_middleware = with_wsgi_middleware

    @staticmethod
    def setup_once() -> None:

        # TODO: A tween is maybe a little bit fragile, so we should
        #       consider the possibility of monkeypatching morepath
        #       or more specifically morepath.App.publish
        #
        # NOTE: We need to be on top of the excview_tween so we
        #       don't forward errors to sentry that have a view
        #       registered. (mostly webob.exc.HTTPException)
        @Framework.tween_factory(over=excview_tween_factory)
        def sentry_tween_factory(
            app: Framework,
            handler: Callable[[CoreRequest], Response]
        ) -> Callable[[CoreRequest], Response]:

            def sentry_tween(request: CoreRequest) -> Response:
                """ Configures scope and starts transaction """

                integration = get_client().get_integration(
                    OneGovCloudIntegration
                )
                if integration is None:
                    return handler(request)

                Scope.get_current_scope().set_transaction_name(
                    request.path,
                    SOURCE_FOR_STYLE[integration.transaction_style]
                )
                Scope.get_isolation_scope().add_event_processor(
                    _make_event_processor(
                        weakref.ref(request), integration
                    )
                )

                try:
                    return handler(request)
                except DB_CONNECTION_ERRORS:
                    # FIXME: This is technically duplicated from
                    #        Framework.handle_exception, maybe it
                    #        would be better to add exception views?
                    #        Since those should be caught by the tween
                    return HTTPServiceUnavailable()
                except Exception:
                    _capture_exception(sys.exc_info())
                    raise

            return sentry_tween

        def with_sentry_middleware(self: Framework) -> bool:
            integration = get_client().get_integration(OneGovCloudIntegration)
            if integration is None:
                return False

            return integration.with_wsgi_middleware

        # add a marker so Framework instances will add the wsgi middleware
        Framework.with_sentry_middleware = property(  # type:ignore
            with_sentry_middleware
        )


class CoreRequestExtractor(RequestExtractor):
    request: CoreRequest

    def env(self) -> WSGIEnvironment:
        return self.request.environ

    def cookies(self) -> RequestCookies:
        return self.request.cookies

    def raw_data(self) -> str:
        return self.request.text

    def form(self) -> dict[str, str]:
        return {
            key: value
            for key, value in self.request.POST.items()
            if isinstance(value, str)
        }

    def files(self) -> dict[str, _FieldStorageWithFile]:
        return {
            key: value
            for key, value in self.request.POST.items()
            if not isinstance(value, str)
        }

    def size_of_file(self, postdata: _FieldStorageWithFile) -> int:
        file = postdata.file
        try:
            return os.fstat(file.fileno()).st_size
        except Exception:
            return 0


def _capture_exception(exc_info: ExcInfo) -> None:
    if exc_info[0] is None or issubclass(exc_info[0], HTTPException):
        return

    event, hint = event_from_exception(
        exc_info,
        client_options=get_client().options,
        mechanism={'type': 'onegov-cloud', 'handled': False},
    )

    capture_event(event, hint=hint)


def _make_event_processor(
    weak_request: Callable[[], CoreRequest | None],
    integration: OneGovCloudIntegration,
) -> EventProcessor:
    def event_processor(event: Event, hint: Hint) -> Event:
        request = weak_request()
        if request is None:
            return event

        with capture_internal_exceptions():
            CoreRequestExtractor(request).extract_into_event(event)
            request_info = event.setdefault('request', {})
            # we override what the base WSGIMiddleware does, since
            # they don't take X_VHM_ROOT into account, so the url
            # contains extra stuff we don't want
            request_info['url'] = request.path_url

            app = request.app
            extra_info = event.setdefault('extra', {})
            extra_info.setdefault('namespace', app.namespace)
            extra_info.setdefault('application_id', app.application_id)

            user_info = event.setdefault('user', {})
            user_id = request.identity.uid if request.identity.userid else None
            user_info.setdefault('id', user_id)
            user_data = user_info.setdefault('data', {})

            if not isinstance(user_data, dict):
                # NOTE: If the user_data is not in a format that we expect
                #       then we just wipe it so we can set our keys
                user_data = user_info['data'] = {}

            user_data.setdefault(
                'role', getattr(request.identity, 'role', 'anonymous'))
            if should_send_default_pii():
                user_info.setdefault(
                    'ip_address', request.environ.get('HTTP_X_REAL_IP'))
                user_info.setdefault('email', request.identity.userid)

        return event

    return event_processor

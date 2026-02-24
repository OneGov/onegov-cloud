from __future__ import annotations

from functools import cached_property


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from typing import Self


class Clipboard:
    """ The clipboard holds a url that should be copied and then pasted.
    The url is expected to be stored in a token that has been created by
    :meth:`onegov.core.request.CoreRequest.new_url_safe_token`.

    The reason behind this is that the url is used to fetch the object behind
    the url in an unrestricted fashion.

    """

    def __init__(self, request: OrgRequest, token: str) -> None:
        self.request = request
        self.token = token

    @cached_property
    def url(self) -> str | None:
        data = self.request.load_url_safe_token(self.token, salt='clipboard')
        return data and data['url'] or None

    def get_object(self) -> Any | None:
        if not self.url:
            return None

        return self.request.app.object_by_path(self.url)

    def clear(self) -> None:
        if self.request.browser_session.has('clipboard_url'):
            del self.request.browser_session['clipboard_url']

    def store_in_session(self) -> None:
        if self.url:
            self.request.browser_session['clipboard_url'] = self.url

    @classmethod
    def from_url(cls, request: OrgRequest, url: str) -> Self:
        return cls(
            request,
            request.new_url_safe_token({'url': url}, salt='clipboard')
        )

    @classmethod
    def from_session(cls, request: OrgRequest) -> Self:
        return cls(
            request,
            request.new_url_safe_token(
                {'url': request.browser_session.get('clipboard_url')},
                salt='clipboard'
            )
        )

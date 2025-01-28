""" Simple redirects for renamed paths using a generic redirect model.

For static paths::

    @App.path('/old-path')
    class OldPathRedirect(Redirect):
        to = '/new-path'

For wildcard paths (e.g. /old-pages/my-page to /new-pages/my-page)::

    @App.path('/old-path', absorb=True)
    class OldPagesRedirect(Redirect):
        to = '/new-pages

"""
from __future__ import annotations

from onegov.core import Framework
from onegov.core.security import Public


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob import Response

    from .request import CoreRequest


class Redirect:
    to: str

    def __init__(self, absorb: str | None = None):
        assert hasattr(self, 'to') and not self.to.endswith('/')

        if absorb:
            self.to = self.to + '/' + absorb


@Framework.view(model=Redirect, permission=Public)
def view_redirect(self: Redirect, request: CoreRequest) -> Response:
    return request.redirect(self.to)

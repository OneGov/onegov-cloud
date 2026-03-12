from __future__ import annotations

from onegov.core.security import Public
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.models import Principal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.request import SwissvotesRequest
    from webob import Response


@SwissvotesApp.html(
    model=Principal,
    template='home.pt',
    permission=Public
)
def view_home(self: Principal, request: SwissvotesRequest) -> Response:
    """ The home page. """

    page = TranslatablePageCollection(request.session).setdefault('home')
    return request.redirect(request.link(page))

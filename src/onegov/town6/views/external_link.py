from __future__ import annotations

from onegov.org.views.external_link import (
    handle_new_external_link, edit_external_link, get_external_link_form)
from onegov.town6 import TownApp
from onegov.core.security import Private
from onegov.town6.layout import DefaultLayout, ExternalLinkLayout
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms.external_link import ExternalLinkForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=ExternalLinkCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_external_link_form
)
def town_handle_new_external_link(
    self: ExternalLinkCollection,
    request: TownRequest,
    form: ExternalLinkForm
) -> RenderData | Response:
    return handle_new_external_link(
        self, request, form, layout=DefaultLayout(self, request)
    )


@TownApp.form(
    model=ExternalLink,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_external_link_form
)
def town_edit_external_link(
    self: ExternalLink,
    request: TownRequest,
    form: ExternalLinkForm
) -> RenderData | Response:
    return edit_external_link(
        self, request, form, layout=ExternalLinkLayout(self, request)
    )

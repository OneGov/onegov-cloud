from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private

from onegov.parliament import _
from onegov.parliament.collections import RISPartyCollection
from onegov.parliament.models import Party

from onegov.town6 import TownApp

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webob import Response

    from onegov.core.request import CoreRequest
    from onegov.core.types import RenderData
    from onegov.parliament.collections.party import PartyCollection
    from onegov.parliament.forms.party import PartyForm
    from onegov.pas.layouts import PASPartyCollectionLayout, PASPartyLayout
    from onegov.town6.layout import RISPartyCollectionLayout, RISPartyLayout


def view_parties(
    self: PartyCollection,
    request: CoreRequest,
    layout: RISPartyCollectionLayout | PASPartyCollectionLayout
) -> RenderData:
    filters = {}
    filters['active'] = [
        Link(
            text=request.translate(title),
            active=self.active == value,
            url=request.link(self.for_filter(active=value))
        ) for title, value in (
            (_('Active'), True),
            (_('Inactive'), False)
        )
    ]

    return {
        'add_link': request.link(self, name='new'),
        'filters': filters,
        'layout': layout,
        'parties': self.query().all(),
        'title': layout.title,
    }


def add_party(
    self: PartyCollection,
    request: CoreRequest,
    form: PartyForm,
    layout: RISPartyCollectionLayout | PASPartyCollectionLayout
) -> RenderData | Response:
    if form.submitted(request):
        party = self.add(**form.get_useful_data())
        request.success(_('Added a new party'))

        return request.redirect(request.link(party))

    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New party'),
        'form': form,
        'form_width': 'large'
    }


def view_party(
    self: Party,
    request: CoreRequest,
    layout: RISPartyLayout | PASPartyLayout
) -> RenderData:

    return {
        'layout': layout,
        'party': self,
        'title': layout.title,
    }


def edit_party(
    self: Party,
    request: CoreRequest,
    form: PartyForm,
    layout: RISPartyLayout | PASPartyLayout
) -> RenderData | Response:
    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []
    layout.include_editor()

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@TownApp.view(
    model=Party,
    request_method='DELETE',
    permission=Private
)
def delete_party(
    self: Party,
    request: CoreRequest
) -> None:
    request.assert_valid_csrf_token()

    collection = RISPartyCollection(request.session)
    collection.delete(self)

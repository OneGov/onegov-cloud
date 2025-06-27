from __future__ import annotations

from webob.exc import HTTPNotFound

from onegov.core.elements import Link
from onegov.core.security import Private, Public

from onegov.parliament.collections import RISPartyCollection
from onegov.parliament.collections import PartyCollection
from onegov.org.forms.party import PartyForm
from onegov.parliament.models import RISParty, Party
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import RISPartyCollectionLayout
from onegov.town6.layout import RISPartyLayout

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.core.request import CoreRequest
    from onegov.pas.layouts import PASPartyCollectionLayout
    from onegov.pas.layouts import PASPartyLayout
    from onegov.town6.request import TownRequest
    from webob import Response


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


@TownApp.html(
    model=RISPartyCollection,
    template='parties.pt',
    permission=Public
)
def ris_view_parties(
    self: RISPartyCollection,
    request: TownRequest
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_parties(self, request, RISPartyCollectionLayout(self, request))


@TownApp.form(
    model=RISPartyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PartyForm
)
def ris_add_party(
    self: RISPartyCollection,
    request: TownRequest,
    form: PartyForm
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return add_party(
        self,
        request,
        form,
        RISPartyCollectionLayout(self, request)
    )


@TownApp.html(
    model=RISParty,
    template='party.pt',
    permission=Public
)
def ris_view_party(
    self: RISParty,
    request: TownRequest
) -> RenderData:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_party(self, request, RISPartyLayout(self, request))


@TownApp.form(
    model=RISParty,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PartyForm
)
def ris_edit_party(
    self: RISParty,
    request: TownRequest,
    form: PartyForm
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return edit_party(self, request, form, RISPartyLayout(self, request))


@TownApp.view(
    model=RISParty,
    request_method='DELETE',
    permission=Private
)
def ris_delete_party(
    self: RISParty,
    request: TownRequest
) -> None:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return delete_party(self, request)

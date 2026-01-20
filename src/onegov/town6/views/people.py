from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.org.views.people import (
    view_people, view_person, handle_new_person, handle_edit_person)
from onegov.town6 import TownApp
from onegov.org.forms import PersonForm

from onegov.people import Person, PersonCollection
from onegov.town6.layout import PersonCollectionLayout, PersonLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(model=PersonCollection, template='people.pt', permission=Public)
def town_view_people(
    self: PersonCollection,
    request: TownRequest
) -> RenderData:
    return view_people(self, request, PersonCollectionLayout(self, request))


@TownApp.html(model=Person, template='person.pt', permission=Public)
def town_view_person(self: Person, request: TownRequest) -> RenderData:
    return view_person(self, request, PersonLayout(self, request))


@TownApp.form(
    model=PersonCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PersonForm
)
def town_handle_new_person(
    self: PersonCollection,
    request: TownRequest,
    form: PersonForm
) -> RenderData | Response:
    return handle_new_person(
        self, request, form, PersonCollectionLayout(self, request))


@TownApp.form(
    model=Person,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PersonForm
)
def town_handle_edit_person(
    self: Person,
    request: TownRequest,
    form: PersonForm
) -> RenderData | Response:
    return handle_edit_person(self, request, form, PersonLayout(self, request))

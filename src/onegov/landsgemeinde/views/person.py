from __future__ import annotations

from onegov.landsgemeinde import _
from onegov.core.security import Private
from onegov.landsgemeinde.app import LandsgemeindeApp
from onegov.org.views.people import handle_new_person, handle_edit_person
from onegov.landsgemeinde.forms import PersonForm
from onegov.town6.layout import PersonLayout, PersonCollectionLayout
from onegov.people import Person, PersonCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


@LandsgemeindeApp.form(
    model=PersonCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PersonForm
)
def landsgemeinde_handle_new_person(
    self: PersonCollection,
    request: LandsgemeindeRequest,
    form: PersonForm
) -> RenderData | Response:

    form.location_code_city.label.text = _('Location')
    layout = PersonCollectionLayout(self, request)
    return handle_new_person(self, request, form, layout)


@LandsgemeindeApp.form(
    model=Person,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PersonForm
)
def landsgemeinde_handle_edit_person(
    self: Person,
    request: LandsgemeindeRequest,
    form: PersonForm
) -> RenderData | Response:

    form.location_code_city.label.text = _('Location')
    layout = PersonLayout(self, request)
    layout.edit_mode = True
    return handle_edit_person(self, request, form, layout)

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import AttendenceCollection
from onegov.pas.forms import AttendenceForm
from onegov.pas.layouts import AttendenceCollectionLayout
from onegov.pas.layouts import AttendenceLayout
from onegov.pas.models import Attendence

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=AttendenceCollection,
    template='attendences.pt',
    permission=Private
)
def view_attendences(
    self: AttendenceCollection,
    request: 'TownRequest'
) -> 'RenderData':

    layout = AttendenceCollectionLayout(self, request)

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'attendences': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=AttendenceCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=AttendenceForm
)
def add_attendence(
    self: AttendenceCollection,
    request: 'TownRequest',
    form: AttendenceForm
) -> 'RenderData | Response':

    if form.submitted(request):
        attendence = self.add(**form.get_useful_data())
        request.success(_("Added a new meeting"))

        return request.redirect(request.link(attendence))

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))

    return {
        'layout': layout,
        'title': _("New meeting"),
        'form': form,
    }


@PasApp.html(
    model=Attendence,
    template='attendence.pt',
    permission=Private
)
def view_attendence(
    self: Attendence,
    request: 'TownRequest'
) -> 'RenderData':

    layout = AttendenceLayout(self, request)

    return {
        'layout': layout,
        'attendence': self,
        'title': layout.title,
    }


@PasApp.form(
    model=Attendence,
    name='edit',
    template='form.pt',
    permission=Private,
    form=AttendenceForm
)
def edit_attendence(
    self: Attendence,
    request: 'TownRequest',
    form: AttendenceForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = AttendenceLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=Attendence,
    request_method='DELETE',
    permission=Private
)
def delete_attendence(
    self: Attendence,
    request: 'TownRequest'
) -> None:

    request.assert_valid_csrf_token()

    collection = AttendenceCollection(request.session)
    collection.delete(self)

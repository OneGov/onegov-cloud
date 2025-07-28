from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import AttendenceCollection
from onegov.pas.forms import AttendenceAddForm
from onegov.pas.forms import AttendenceAddPlenaryForm
from onegov.pas.forms import AttendenceForm
from onegov.pas.layouts import AttendenceCollectionLayout
from onegov.pas.layouts import AttendenceLayout
from onegov.pas.models import Attendence
from onegov.pas.models import Change

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
    request: TownRequest
) -> RenderData:

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
    form=AttendenceAddForm
)
def add_attendence(
    self: AttendenceCollection,
    request: TownRequest,
    form: AttendenceAddForm
) -> RenderData | Response:

    if form.submitted(request):
        attendence = self.add(**form.get_useful_data())
        Change.add(request, 'add', attendence)
        request.success(_('Added a new attendence'))

        return request.redirect(request.link(attendence))

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))

    return {
        'layout': layout,
        'title': _('New attendence'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.form(
    model=AttendenceCollection,
    name='new-bulk',
    template='form.pt',
    permission=Private,
    form=AttendenceAddPlenaryForm
)
def add_plenary_attendence(
    self: AttendenceCollection,
    request: TownRequest,
    form: AttendenceAddPlenaryForm
) -> RenderData | Response:

    if form.submitted(request):
        data = form.get_useful_data()
        parliamentarian_ids = data.pop('parliamentarian_id')
        for parliamentarian_id in parliamentarian_ids:
            attendence = self.add(
                parliamentarian_id=parliamentarian_id, **data
            )
            Change.add(request, 'add', attendence)
        request.success(_('Added plenary session'))

        return request.redirect(request.link(self))

    layout = AttendenceCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New plenary session'), '#'))

    return {
        'layout': layout,
        'title': _('New plenary session'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.html(
    model=Attendence,
    template='attendence.pt',
    permission=Private
)
def view_attendence(
    self: Attendence,
    request: TownRequest
) -> RenderData:

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
    request: TownRequest,
    form: AttendenceForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        Change.add(request, 'edit', self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = AttendenceLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
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
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    Change.add(request, 'delete', self)
    collection = AttendenceCollection(request.session)
    collection.delete(self)
